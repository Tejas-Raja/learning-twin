# 🧠 Student Learning Twin

An **AI-powered Digital Twin of a student's learning brain**.

This prototype learns how a student studies by tracking:

- ⏱ Time taken per question  
- ✅ Correct vs incorrect answers  
- 📚 Weak chapters and topics  
- 📈 Difficulty tolerance over time  

Using this data, it generates:

- A **personalized learning profile**
- **Predicted weak areas**
- **Adaptive question difficulty** (easier or harder based on performance)
- Simple **analytics dashboards** (accuracy & timing graphs)

---

## 🚀 Tech Stack

- **Frontend + Backend:** [Streamlit](https://streamlit.io/)
- **Language:** Python 3
- **Database:** SQLite (local `learning_twin.db`)
- **Data / Analytics:** pandas
- **ML (planned):** scikit-learn model for performance prediction

---

## 📂 Project Structure

```bash
student-learning-twin/
├── app.py             # Main Streamlit app
├── questions.json     # Question bank (with topic, chapter, difficulty metadata)
├── learning_twin.db   # SQLite database (auto-created on first run)
├── requirements.txt   # Python dependencies
├── .gitignore
└── README.md