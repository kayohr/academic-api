require('./config/env')

const fastify = require('fastify')({
  logger: {
    level: process.env.LOG_LEVEL || 'info',
    transport:
      process.env.NODE_ENV !== 'production'
        ? { target: 'pino-pretty', options: { colorize: true } }
        : undefined,
    redact: ['req.headers.authorization'],
  },
})

const errorHandler = require('./shared/errors/errorHandler')
const pool = require('./config/database')
const env = require('./config/env')

async function buildApp() {
  // Security headers
  await fastify.register(require('@fastify/helmet'))

  // Rate limiting
  await fastify.register(require('@fastify/rate-limit'), {
    max: 100,
    timeWindow: '1 minute',
  })

  // JWT
  await fastify.register(require('@fastify/jwt'), {
    secret: env.jwt.secret,
  })

  // Global error handler
  fastify.setErrorHandler(errorHandler)

  // Health check
  fastify.get('/health', async (request, reply) => {
    try {
      await pool.query('SELECT 1')
      return { status: 'ok', db: 'ok', timestamp: new Date().toISOString() }
    } catch {
      reply.status(503).send({ status: 'error', db: 'unreachable' })
    }
  })

  fastify.get('/health/ready', async (request, reply) => {
    try {
      await pool.query('SELECT 1')
      return { ready: true }
    } catch {
      reply.status(503).send({ ready: false })
    }
  })

  fastify.get('/health/live', async () => ({ alive: true }))

  return fastify
}

async function start() {
  const app = await buildApp()
  try {
    await app.listen({ port: env.port, host: '0.0.0.0' })
    app.log.info(`Server running on port ${env.port}`)
  } catch (err) {
    app.log.error(err)
    process.exit(1)
  }
}

start()
