# 🤖 AI News Aggregator

> Autonomous agentic system delivering daily AI news digests via email

## 📋 Project Overview

An intelligent system that autonomously:
- Fetches AI news from YouTube channels (transcripts) and company blogs
- Processes and summarizes content using Google Gemini AI
- Curates and scores content for relevance and quality
- Delivers personalized daily email digests with source links

**Built entirely on free tiers** - Gemini, Resend, Render PostgreSQL

---

## 🎯 High-Level Architecture Plan
```
┌─────────────────────────────────┐
│     Orchestrator Agent          │
│  (Coordinates all operations)   │
└────────────┬────────────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌─────────┐      ┌──────────┐
│ YouTube │      │   Blog   │
│  Agent  │      │  Agent   │
└────┬────┘      └────┬─────┘
     │                │
     └────────┬───────┘
              ▼
    ┌──────────────────┐
    │ Content Processor│
    │     Agent        │
    │ - Summarize      │
    │ - Deduplicate    │
    │ - Score quality  │
    └────────┬─────────┘
             ▼
    ┌──────────────────┐
    │ Digest Generator │
    │     Agent        │
    │ - Select top 10  │
    │ - Build email    │
    │ - Include links  │
    └──────────────────┘
```

---

## 📰 Content Sources

### **YouTube Channels**
- Two Minute Papers
- Yannic Kilcher
- AI Explained
- Matthew Berman
- (Configurable in `.env`)

### **Company Blogs**
- OpenAI Blog
- Anthropic News
- Google DeepMind Blog
- Meta AI Blog
- Hugging Face Blog
- Stability AI News
- (Configurable in `.env`)

### **Tech News**
- TechCrunch AI
- VentureBeat AI
- The Verge AI

---

## 🔑 Required API Keys

All free tier:

1. **Google Gemini**
   - Sign up: https://makersuite.google.com/app/apikey
   - Free: 60 requests/minute

2. **Resend**
   - Sign up: https://resend.com/api-keys
   - Free: 3,000 emails/month

3. **PostgreSQL** (via Render)
   - Sign up: https://render.com
   - Free: 1GB storage



**This README will be updated as features are implemented.**