/**
 * Supabase client initialization for frontend
 */

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.39.0/+esm'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://fwpgqgsetaptekhqskti.supabase.co'
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || 'sb_publishable_1X6he5_6-5n9cZ3S_fU5nQ_Xsdeqyma'

export const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

/**
 * Sign up with email
 */
export async function signUp(email, password) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  })
  return { data, error }
}

/**
 * Sign in with email
 */
export async function signIn(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  return { data, error }
}

/**
 * Sign out
 */
export async function signOut() {
  const { error } = await supabase.auth.signOut()
  return { error }
}

/**
 * Get current user
 */
export async function getCurrentUser() {
  const { data: { user }, error } = await supabase.auth.getUser()
  return { user, error }
}

/**
 * Store analysis in database
 */
export async function storeAnalysis(userId, fileName, analysisResult) {
  const { data, error } = await supabase
    .from('analyses')
    .insert([
      {
        user_id: userId,
        file_name: fileName,
        result: analysisResult,
      },
    ])
    .select()
  return { data, error }
}

/**
 * Get user's analyses
 */
export async function getUserAnalyses(userId) {
  const { data, error } = await supabase
    .from('analyses')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
  return { data, error }
}

/**
 * Upload file to storage
 */
export async function uploadFileToStorage(bucketName, filePath, file, userId) {
  const fullPath = `${userId}/${filePath}`
  const { data, error } = await supabase.storage
    .from(bucketName)
    .upload(fullPath, file, { upsert: true })
  return { data, error }
}

/**
 * Subscribe to real-time analysis updates
 */
export function subscribeToAnalyses(userId, callback) {
  const subscription = supabase
    .from('analyses')
    .on('*', (payload) => {
      if (payload.new.user_id === userId) {
        callback(payload)
      }
    })
    .subscribe()
  return subscription
}
