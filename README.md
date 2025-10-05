# TalentScout-Hiring-Assistant
TalentScout is a Streamlit-based hiring assistant that streamlines candidate screening by automatically generating tailored technical interview questions. It uses Google Gemini AI to create context-aware questions based on the candidate's tech stack, experience level, and desired position, with intelligent fallback templates for offline use.
# TalentScout Hiring Assistant

An intelligent candidate screening application that helps recruiters and hiring managers generate customized technical interview questions automatically.

## 🎯 What It Does

TalentScout collects candidate information and generates 3-5 technical questions per technology in their stack, tailored to their experience level and desired position. It uses Google's Gemini AI for intelligent question generation and falls back to curated templates when needed.

## ✨ Key Features

- **Smart Candidate Forms** - Collect all necessary information in one screen
- **AI-Powered Questions** - Gemini API generates context-aware technical questions
- **Fallback Templates** - Pre-written questions for Python, Django, React, SQL, and AWS
- **Interactive Chat** - Regenerate questions or view candidate info on demand
- **Privacy First** - Automatically anonymizes email and phone data
- **Easy Setup** - Simple Streamlit interface, runs locally

## 🚀 Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Set your Gemini API key
export GEMINI_API_KEY=your_key_here

# Run the application
streamlit run tes1.py
