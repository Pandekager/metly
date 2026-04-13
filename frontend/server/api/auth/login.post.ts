import jwt from 'jsonwebtoken'
import type { Login } from '~/types/login'

export default defineEventHandler(async (event) => {
  const body = await readBody<Login>(event)
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase

  const url = new URL('auth/login', apiBase.replace('/api', '')).toString()
  let userId: string

  console.log('Attempting login for email:', body.email)

  try {
    const response: { user_id: string } = await $fetch(url, {
      method: 'POST',
      body: {
        email: body.email,
        password: body.password
      }
    })
    userId = response.user_id
  } catch (error: any) {
    console.error('Login error:', error)
    throw createError({
      statusCode: 401,
      message: 'Forkert e-mail eller adgangskode'
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
