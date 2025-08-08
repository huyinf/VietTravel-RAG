import PyPDF2
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import torch
from transformers import GenerationConfig, LlamaForCausalLM, LlamaTokenizer, LlamaConfig

# --- PDF Text Extraction ---
def extract_text_from_pdf(pdf_path):
  """Extract text from a PDF file using PyPDF2."""
  corpus = []
  with open(pdf_path, "rb") as file:
      reader = PyPDF2.PdfReader(file)
      for page in reader.pages:
          text = page.extract_text()
          if text:  # Ensure there's text on the page
              corpus.append({"passage": text.strip()})
  return corpus

# --- Embedding Model Loading ---
# Load the Sentence Transformer model for generating embeddings
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# --- FAISS Index Creation ---
def create_faiss_index(corpus):
  """Create a FAISS index for storing embeddings."""
  passages = [doc["passage"] for doc in corpus]
  embeddings = embedding_model.encode(passages, show_progress_bar=True)
  embeddings = np.array(embeddings, dtype="float32")
  faiss.normalize_L2(embeddings)

  dimension = embeddings.shape[1]
  index = faiss.IndexFlatIP(dimension)  # Inner product index for cosine similarity
  index.add(embeddings)
  return index, passages

# --- Vector Search with FAISS ---
def retrieve_with_faiss(question, faiss_index, passages, topk=3):
  """
  Retrieve the most relevant passages using FAISS and vector similarity.
  """
  question_embedding = embedding_model.encode([question])
  faiss.normalize_L2(question_embedding)
  distances, indices = faiss_index.search(question_embedding, topk)

  # Retrieve top-k passages
  retrieved = [{"passage": passages[idx], "score": distances[0][i]} for i, idx in enumerate(indices[0])]
  return retrieved

# --- Prompt Construction ---
prompt_template = (
  "### System:\n"
  "Below is an instruction that describes a task, paired with an input that provides further context. "
  "Write a response that appropriately completes the request.\n\n\n\n"
  "### Instruction:\n{instruction}\n\n"
  "### Input:\n{input}\n\n"
  "### Response:\n{output}"
)

def get_prompt(question, contexts):
  """Generate a prompt for the language model."""
  context = "\n\n".join([f"Context [{i+1}]: {x['passage']}" for i, x in enumerate(contexts)])
  instruction = 'You are an AI assistant. Provide a detailed answer so user don’t need to search outside to understand the answer.'
  input = f"Dựa vào một số ngữ cảnh được cho dưới đây, trả lời câu hỏi ở cuối.\n\n{context}\n\nQuestion: {question}\nHãy trả lời chi tiết và đầy đủ."
  prompt = prompt_template.format(
      instruction=instruction,
      input=input,
      output=''
  )
  return prompt

# --- LLM Model Loading ---
torch_dtype = torch.bfloat16
model_id = "llm4fun/vietrag-7b-v1.0"
device = "cuda"

tokenizer = LlamaTokenizer.from_pretrained(model_id)
model = LlamaForCausalLM.from_pretrained(
    model_id,
    config=LlamaConfig.from_pretrained(model_id),
    torch_dtype=torch_dtype
)
model = model.eval().to(device)

def generate(prompt, max_new_tokens=1024):
  """
  Generate a text response from the language model using the provided prompt.
  """
  input_ids = tokenizer(prompt, return_tensors="pt")["input_ids"].to(model.device)
  
  # Perform text generation
  with torch.no_grad():
    generation_config = GenerationConfig(
      repetition_penalty=1.13,
      max_new_tokens=max_new_tokens,
      pad_token_id=tokenizer.pad_token_id,
      do_sample=False,
      use_cache=True,
    )
    generated = model.generate(
      inputs=input_ids,
      generation_config=generation_config,
    )

  # Get the generated tokens, starting from where the input ends
  gen_tokens = generated.cpu()[:, input_ids.shape[-1]:]  # Slice from the input length onward
  output = tokenizer.batch_decode(gen_tokens)[0]
  return output.strip()

# --- RAG Pipeline ---
def rag_pipeline(question, faiss_index, passages, topk=3):
  """
  End-to-end pipeline for retrieval-augmented generation (RAG).
  """
  # Retrieve relevant contexts
  top_passages = retrieve_with_faiss(question, faiss_index, passages, topk=topk)
  # Generate a prompt
  prompt = get_prompt(question, top_passages)
  # Generate answer using the LLM
  generated_answer = generate(prompt)
  result = {
      "retrieved_context": top_passages,
      "generated_answer": generated_answer
  }
  return result

# --- Main Code Execution ---
if __name__ == "__main__":
  # Path to your PDF file
  pdf_path = "/home/jupyter-trunglph/Others/RAG/21120157_21120415.pdf"  # Replace with your PDF path

  # Step 1: Extract the text corpus from the PDF
  meta_corpus = extract_text_from_pdf(pdf_path)
  print("Meta corpus size:", len(meta_corpus))

  # Step 2: Create a FAISS index with the corpus
  faiss_index, passages = create_faiss_index(meta_corpus)

  # Step 3: Define questions to ask
  questions = [
      "Federated Learning là gì?",
      "Resnet18 là gì?",
      "Adversarial Training là gì?",
  ]

  # Step 4: Answer each question using RAG
  for question in questions:
    print(f"\n\n{'='*50}")
    print(f"\nQuestion: {question}")
    result = rag_pipeline(question, faiss_index, passages, topk=3)

    print("\nGenerated Answer:")
    print(result["generated_answer"])
