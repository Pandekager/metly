export default defineEventHandler(async (event) => {
  const token = getCookie(event, 'jwt')
  
  if (!token) {
    return {
      authenticated: false,
      message: 'No JWT token found in cookies',
      user: null
    }
  }

  const config = useRuntimeConfig(event)

  try {
    const payload = await new Promise<any>((resolve, reject) => {
      import('jsonwebtoken').then(({ default: jwt }) => {
        jwt.verify(token, config.jwtSecret, (err, decoded) => {
          if (err) reject(err)
          else resolve(decoded)
        })
      }).catch(reject)
    })

    if (!payload?.sub || !payload?.email) {
      return {
        authenticated: false,
        message: 'JWT payload missing expected fields',
        user: null
      }
    }

    return {
      authenticated: true,
      message: 'JWT token found',
      user: {
        id: payload.sub,
        email: payload.email
      }
    }
  } catch {
    deleteCookie(event, 'jwt', { path: '/' })
    return {
      authenticated: false,
      message: 'Invalid JWT token',
      user: null
    }
  }
})
