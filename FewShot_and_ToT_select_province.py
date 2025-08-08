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


# --- Improved Prompt with Tree-of-Though ---
prompt_template = """
### Instructions:
You are an AI assistant. Use *Tree of Thought (ToT)* reasoning to analyze multiple perspectives before generating a complete response.
Each thought branch should:
- Identify a unique approach to answering the question.
- Reason step by step.
- Evaluate logical consistency.
- Combine the best insights to form a well-structured response.
- Translate the answer into the language of the question.

### Context:
{context}

### Question:
{question}

### Example Tree of Thought:

*Q:* How to plan a travel itinerary and enjoy local cuisine in Hanoi?

* - Based on historical data & traveler reviews:*  
A typical 3-day itinerary in Hanoi includes exploring the Old Quarter, Hoan Kiem Lake, and famous landmarks such as the Ho Chi Minh Mausoleum. Visitors should also experience traditional water puppet shows and take a cyclo tour.  

* - Analyzing local food specialties:*  
Hanoi is famous for dishes like *Pho, Bun Cha, and Egg Coffee*. A food tour covering local street vendors and hidden gems is highly recommended for an authentic experience.  

* - Considering budget & travel season:*  
The best time to visit is *autumn (September–November) and spring (March–April)* when the weather is cool. Travelers on a budget can explore street food stalls and local homestays to optimize costs.  

*A:*  
For a complete Hanoi travel experience, *explore historical sites*, *enjoy street food tours*, and *visit in autumn or spring* for the best weather.  

---

*Q:* What are the most interesting attractions to visit in Hai Phong?

* - Based on popular tourist destinations:*  
Hai Phong is known for *Do Son Beach, Cat Ba Island, and Lan Ha Bay*, offering beautiful coastal scenery and various water activities.  

* - Analyzing cultural and historical significance:*  
Historical sites such as *Trang Kenh relic site, Hang Kenh Communal House, and Du Hang Pagoda* provide insight into the city's rich heritage.  

* - Considering travel experience & adventure:*  
Cat Ba National Park is perfect for nature lovers, while Do Son Casino attracts visitors looking for entertainment. The *Buffalo Fighting Festival in Do Son (September)* is a must-see cultural event.  

*A:*  
Hai Phong’s top attractions include *Cat Ba Island, Do Son Beach, and Trang Kenh relic site*. For adventure seekers, Cat Ba National Park is ideal.  

---

*Q:* What are the must-try specialty dishes in Da Nang?

*- Researching the city's culinary highlights:*  
Da Nang is famous for *Mi Quang (turmeric-infused noodles with shrimp and pork), Bun Cha Ca (fish cake noodle soup), and Banh Xeo (crispy Vietnamese pancakes)*.  

*- Understanding local dining culture:*  
Street food stalls and traditional restaurants offer the best authentic flavors. *Han Market and Con Market* are great spots to try multiple dishes at affordable prices.  

*- Considering seasonal specialties:*  
Seafood is a must-try in Da Nang, with fresh catches like *grilled stingray, squid, and clams* available throughout the year.  

*A:*  
The must-try dishes in Da Nang include *Mi Quang, Bun Cha Ca, and Banh Xeo*. For an authentic experience, visit local markets and seafood restaurants.  

---

*Q:* When is the best time to travel to Can Tho?

* - Considering customer reviews:*  
Can Tho is famous for the Cai Rang floating market, fruit orchards, and its waterways. The peak fruit season is from June to August.

* - Weather conditions:*  
Can Tho has two seasons: the rainy season (May to November) and the dry season (December to April). The dry season is suitable for easy travel and visiting the floating markets.

* - Economic factors & experiences:*  
Summer (June to August) offers plenty of fruits and lively activities, but it is also the peak tourist season. If you want to avoid crowds, November to December is a good choice.

*A:*  
The ideal time to travel to Can Tho is *December to April* to enjoy the dry weather and ease of movement. If you want to experience the fruit season, you can visit in *June to August*.

---

### Answer:
---
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
