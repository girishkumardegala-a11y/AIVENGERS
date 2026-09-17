# Supabase Setup Guide

## Database Tables

Run these SQL commands in Supabase SQL Editor to set up the required tables:

### 1. Users Profiles Table
```sql
CREATE TABLE user_profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE,
  email TEXT UNIQUE,
  full_name TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (id)
);
```

### 2. Analyses Table (stores job description analysis results)
```sql
CREATE TABLE analyses (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users ON DELETE CASCADE,
  file_name TEXT NOT NULL,
  result JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON DELETE CASCADE
);

CREATE INDEX analyses_user_id_idx ON analyses(user_id);
CREATE INDEX analyses_created_at_idx ON analyses(created_at);
```

### 3. Storage Bucket
Create a storage bucket named `job-descriptions`:
- Go to Supabase Dashboard
- Click "Storage" in the left sidebar
- Click "Create a new bucket"
- Name it: `job-descriptions`
- Make it public or private based on your needs

## Environment Setup

Create a `.env` file in the `backend/` directory:

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
CLAUDE_MODEL=claude-sonnet-5
SUPABASE_URL=https://fwpgqgsetaptekhqskti.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_1X6he5_6-5n9cZ3S_fU5nQ_Xsdeqyma
```

Create a `.env.local` file in the `frontend/` directory:

```env
VITE_SUPABASE_URL=https://fwpgqgsetaptekhqskti.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_1X6he5_6-5n9cZ3S_fU5nQ_Xsdeqyma
```

## Features Enabled

✅ **Authentication** - User signup/signin via Supabase Auth  
✅ **Database** - Store analysis results and user data  
✅ **Storage** - Upload and store job description files  
✅ **Real-time** - Subscribe to real-time analysis updates  

## Backend Endpoints

- `POST /api/analyses` - Save analysis result
- `GET /api/analyses/{user_id}` - Get user's analyses
- `POST /api/upload` - Upload file to storage

## Frontend Functions

```javascript
import { 
  signUp, 
  signIn, 
  getCurrentUser, 
  storeAnalysis, 
  getUserAnalyses, 
  uploadFileToStorage,
  subscribeToAnalyses 
} from './supabase.js'
```
