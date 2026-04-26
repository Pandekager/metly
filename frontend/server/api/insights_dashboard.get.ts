import { defineEventHandler } from 'h3'
import { useRuntimeConfig } from '#app'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const apiBase = process.env.API_BASE || config.public.apiBase || 'http://127.0.0.1:8000/api'

  // Get auth token from cookie or Authorization header
  const authHeader = getHeader(event, 'authorization')
  const cookieHeader = getHeader(event, 'cookie')

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (authHeader) {
    headers['Authorization'] = authHeader
  }

  if (cookieHeader) {
    headers['Cookie'] = cookieHeader
  }

  try {
    const response = await $fetch(`${apiBase}/insights_dashboard`, {
      headers,
    })
    return response
  } catch (error: any) {
    console.error('Proxy error for /api/insights_dashboard:', error)
    throw createError({
      statusCode: error.response?.status || 500,
      message: error.message || 'Failed to fetch insights dashboard',
    })
  }
})