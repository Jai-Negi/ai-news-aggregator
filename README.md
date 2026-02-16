# AI News Aggregator

This project automatically collects the latest updates in Artificial Intelligence and sends a daily email summary.

The goal is to help users stay informed about important AI developments without spending time browsing multiple websites and channels.

## Overview

The system performs the following steps:
- Collects AI-related content from YouTube, company blogs, and tech news websites
- Extracts the main information from each source
- Summarizes the content using Google Gemini
- Filters and removes duplicate or low-value updates
- Selects the most relevant news
- Sends a daily email digest with links to the original sources

## Data Sources

Content is gathered from:
- AI-focused YouTube channels (using transcripts)
- Official AI company blogs such as OpenAI, Google DeepMind, Meta AI, etc.
- Tech news platforms like TechCrunch and VentureBeat

Sources can be configured using environment variables.

## Tech Stack

- Python
- Google Gemini API (for summarization)
- PostgreSQL (data storage)
- Resend (email delivery)
- Docker and Docker Compose

The project is designed to run using free-tier services.

## How It Works (High Level)

1. Fetch new AI content from configured sources  
2. Process and summarize the content  
3. Score and filter based on relevance  
4. Generate a daily news digest  
5. Send the digest via email  

## Setup

1. Clone the repository
   git clone https://github.com/Jai-Negi/ai-news-aggregator.git

2. Move into the project folder
   cd ai-news-aggregator

3. Create a .env file and add the required API keys and configuration (refer to .env.example)

4. Run the project using Docker
   docker-compose up --build

## Purpose

This project was built to practice:
- Building end-to-end AI workflows
- Using Large Language Models for real-world use cases
- Automating data collection and processing
- Designing a production-style system
