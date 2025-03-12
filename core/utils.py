import fitz  # PyMuPDF
import os
import requests
import json

# ✅ Groq API Config
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def extract_text_from_file(file_path):
    """Ensure full extraction from PDFs, TXT, CPP, PY, and other formats."""
    
    text = ""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text("text") + "\n"
    
    elif ext in [".txt", ".cpp", ".py", ".java", ".sql"]:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    # ✅ Ensure extracted text is **not empty**
    if not text.strip():
        print(f"❌ Warning: No readable content extracted from {file_path}")
    
    return text.strip()


def generate_correct_answers(questions_text):
    """Use Groq AI to generate correct answers."""
    
    payload = {
        "model": "llama3-70b-8192",
        "temperature": 0,  # ✅ Ensures consistent and repeatable results
        "messages": [
            {"role": "system", "content": "You are an expert exam grader."},
            {"role": "user", "content": f"Here are the exam questions:\n{questions_text}\nProvide the ideal correct answers."}
        ]
    }
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    response = requests.post(GROQ_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return None

def grade_exam(correct_answers, student_answers, exam_text):
    """Use Groq AI to fairly and strictly grade each question separately and sum up the total score."""

    payload = {
        "model": "llama3-70b-8192",
        "temperature": 0,  # ✅ Ensures **deterministic** grading
        "messages": [
            {"role": "system", "content": """
            You are an **expert university professor** grading **informatics and computer science** exams.  
Your grading must be **strict, consistent, and fair** while rewarding valid attempts.  

## 📌 **Grading Rules**
- Compare **each student answer** **directly** with the **correct answer**.
- **Grade each question individually based on its assigned weight.**
- **Only assign full points if the answer is 100% correct.**
- **Give partial points for valid attempts**, even if they contain small mistakes.
- **Ensure the grading is stable, reliable, and repeatable.**
- **Return a JSON list of scores (one per question), using the correct weight per question.**

## ⚠️ **Adaptive Scoring Breakdown**
- ✅ **Fully correct (100% accurate, no mistakes) → Full question weight**  
- ⚠️ **Mostly correct (minor mistake, but approach is valid) → Partial weight**  
- 🔹 **Partially correct (some valid logic but incomplete/wrong approach) → Lower partial weight**  
- ❌ **Incorrect but somewhat relevant attempt (syntax correct but incorrect logic) → Minimal weight**  
- 🚫 **Completely irrelevant or empty answer → 0 points**  

## 🚨 **IMPORTANT RULES**
- **DO NOT return a single total score.**
- **Return ONLY a JSON list of individual question scores like:**  
  `[7, 2, 4, 8]`
- **Use the correct weight for each question instead of a fixed 5-point scale.**
- **DO NOT explain or summarize the grades.**
- **DO NOT add any extra text.**

---

## **📝 Example**
**Exam Question:**  
_"Write a function to check if a number is even or odd. (8 points)"_

**Correct Answer:**  
```cpp
bool isEven(int num) {
    return num % 2 == 0;
}
`**
            - **DO NOT include explanations.**
            """},
            {"role": "user", "content": f"""
            **Exam Content:**
            {exam_text}

            **Correct Answers:**
            {correct_answers}

            **Student's Answers:**
            {student_answers}

            **Grading Instructions:**
            - **Grade each question individually (out of 5).**
            - **Return a JSON list like this: `[5, 3, 4, 5]`**
            - **DO NOT summarize. DO NOT add explanations.**
            """}
        ]
    }
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    
    # 📌 **DEBUG: Log request sent to Groq**
    print("\n🚀 Sending to Groq API:\n", json.dumps(payload, indent=4))

    response = requests.post(GROQ_URL, json=payload, headers=headers)

    # 📌 **DEBUG: Log Groq response**
    print("\n🔎 Groq API Response:", response.text)

    if response.status_code == 200:
        try:
            raw_score_list = response.json()["choices"][0]["message"]["content"].strip()
            scores = json.loads(raw_score_list)  # ✅ Convert JSON string to Python list
            
            if isinstance(scores, list) and all(isinstance(s, (int, float)) for s in scores):
                total_score = round(sum(scores), 1)

                # ✅ Ensure fair grading logic
                if total_score > 20:  # Prevent over-scoring
                    total_score = 20
                elif total_score < 5 and any(score > 0 for score in scores):  # Avoid unfairly low scores
                    total_score = max(5, total_score)

                return total_score  # ✅ Final adjusted score

        except Exception as e:
            print(f"❌ Error parsing AI response: {e}")

    return 4.0  # ✅ Default if AI request fails
