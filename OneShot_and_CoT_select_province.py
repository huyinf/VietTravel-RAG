import PyPDF2
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, CrossEncoder
import faiss
import numpy as np
from langchain.schema import Document
import torch
from transformers import LlamaForCausalLM, LlamaTokenizer, BitsAndBytesConfig
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
import streamlit as st
from rank_bm25 import BM25Okapi

st.title("Du lịch và Ẩm thực Việt Nam")

# --- Load LLM Model Efficiently ---
@st.cache_resource
def load_llm_and_tokenizer():
    model_id = "llm4fun/vietrag-7b-v1.0"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = LlamaTokenizer.from_pretrained(model_id)
    quant_config = BitsAndBytesConfig(load_in_4bit=True)
    model = LlamaForCausalLM.from_pretrained(model_id, quantization_config=quant_config).to(device).eval()
    return model, tokenizer, device

model, tokenizer, device = load_llm_and_tokenizer()

# --- Improved Vector Store with Hybrid Search (FAISS + BM25) ---
@st.cache_resource
def create_vector_store(pdf_path):
    def extract_text_from_pdf(pdf_path):
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            return [page.extract_text().strip() for page in reader.pages if page.extract_text()]
    
    raw_texts = extract_text_from_pdf(pdf_path)
    docs = [Document(page_content=text) for text in raw_texts]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(docs)

    embedding_model = SentenceTransformer("all-mpnet-base-v2")
    bm25 = BM25Okapi([doc.page_content.split() for doc in all_splits])  # BM25 Index

    def embed_documents(texts):
        return embedding_model.encode(texts, convert_to_tensor=True).cpu().numpy()

    dimension = embedding_model.get_sentence_embedding_dimension()
    index = faiss.IndexFlatL2(dimension)
    vector_store = FAISS(embedding_function=embed_documents, index=index, docstore=InMemoryDocstore(), index_to_docstore_id={})
    vector_store.add_documents(all_splits)
    return vector_store, embedding_model, bm25, all_splits

provinces = [
    "AnGiang", "BaRiaVungTau", "BacGiang", "BacKan", "BacLieu", "BacNinh", "BenTre", 
    "BinhDinh", "BinhDuong", "BinhPhuoc", "BinhThuan", "CaMau", "CanTho", "CaoBang", 
    "DaNang", "DakLak", "DakNong", "DienBien", "DongNai", "DongThap", "GiaLai", 
    "HaGiang", "HaNam", "HaNoi", "HaTinh", "HaiDuong", "HaiPhong", "HauGiang", 
    "HoChiMinh", "HoaBinh", "HungYen", "KhanhHoa", "KienGiang", "KonTum", "LaiChau", 
    "LamDong", "LangSon", "LaoCai", "LongAn", "NamDinh", "NgheAn", "NinhBinh", 
    "NinhThuan", "PhuTho", "PhuYen", "QuangBinh", "QuangNam", "QuangNgai", 
    "QuangNinh", "QuangTri", "SocTrang", "SonLa", "TayNinh", "ThaiBinh", 
    "ThaiNguyen", "ThanhHoa", "ThuaThienHue", "TienGiang", "TraVinh", "TuyenQuang", 
    "VinhLong", "VinhPhuc"
]

selected_province = st.selectbox("Chọn tỉnh:", provinces)
pdf_path = f"data/{selected_province}.pdf"
vector_store, embedding_model, bm25, all_splits = create_vector_store(pdf_path)

# --- Hybrid Retrieval (FAISS + BM25 + Reranking) ---
def retrieve(question, topk=5):
    bm25_scores = bm25.get_scores(question.split())
    top_bm25_indices = np.argsort(bm25_scores)[-topk:][::-1]
    faiss_results = vector_store.similarity_search(question, k=topk)
    hybrid_results = [all_splits[i] for i in top_bm25_indices] + faiss_results
    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    reranked = sorted(hybrid_results, key=lambda doc: reranker.predict([question, doc.page_content]), reverse=True)
    return reranked[:topk]

# --- Improved Prompt with Few-shot & Chain-of-Thought (CoT) ---
prompt_template = """
### Instruction:
You are an AI assistant. Provide a detailed answer based on the given contexts.
Use structured information and reasoning to generate a complete response.

### Contexts:
{context}

### Question:
{question}

### Example Response:
**Q:** What is the best time to visit HaLong Bay?
**A:** The best time to visit HaLong Bay is from **October to April** when the weather is cool and dry. Avoid June to August due to typhoons.

### Answer:
"""

def get_prompt(question, contexts):
    context_text = "\n\n".join([f"Context [{i+1}]: {x.page_content}" for i, x in enumerate(contexts)])
    return prompt_template.format(context=context_text, question=question)

def generate(prompt, max_new_tokens=1024):
    input_ids = tokenizer(prompt, return_tensors="pt")["input_ids"].to(device)
    with torch.no_grad():
        generated = model.generate(input_ids, max_new_tokens=max_new_tokens, pad_token_id=tokenizer.pad_token_id, repetition_penalty=1.13)
    return tokenizer.batch_decode(generated[:, input_ids.shape[-1]:], skip_special_tokens=True)[0]

# --- RAG Pipeline ---
def rag_pipeline(question, topk=5):
    top_passages = retrieve(question, topk)
    prompt = get_prompt(question, top_passages)
    generated_answer = generate(prompt)
    return {"retrieved_context": top_passages, "generated_answer": generated_answer}

# --- Streamlit UI ---
user_question = st.text_input(f"Nhập câu hỏi của bạn về {selected_province}:")
if st.button("Hỏi"):
    if user_question:
        with st.spinner("Đang xử lý..."):
            result = rag_pipeline(user_question, topk=5)
            st.write("**Câu trả lời:**")
            st.write(result["generated_answer"])
            with st.expander("Ngữ cảnh được sử dụng"):
                for i, context in enumerate(result["retrieved_context"]):
                    st.write(f"**Ngữ cảnh {i+1}:**")
                    st.write(context.page_content)
    else:
        st.warning("Vui lòng nhập câu hỏi.")