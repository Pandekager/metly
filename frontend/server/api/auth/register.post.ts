import jwt from 'jsonwebtoken'

interface RegisterBody {
  email: string
  password: string
  platform: 'shopify' | 'dandomain' | 'dandomain classic'
}

export default defineEventHandler(async (event) => {
  const body = await readBody<RegisterBody>(event)
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase
  const url = new URL('auth/register', apiBase.replace('/api', '')).toString()

  let userId: string

  try {
    const response: { user_id: string } = await $fetch(url, {
      method: 'POST',
      body: {
        email: body.email,
        password: body.password,
        platform: body.platform
      }
    })
    userId = response.user_id
  } catch (error: any) {
    throw createError({
      statusCode: error?.statusCode || 500,
      message: error?.data?.detail || error?.message || 'Failed to create account'
    })
  }

  const secret = config.jwtSecret
  const payload = {
    sub: userId,
    email: body.email,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 60 * 60 * 24
  }

  const token = jwt.sign(payload, secret, { algorithm: 'HS256' })

  setCookie(event, 'jwt', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24,
    path: '/'
  })

  return {
    success: true,
    token,
    user: {
      id: userId,
      email: body.email
    }
  }
})
