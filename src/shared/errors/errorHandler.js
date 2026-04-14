const { AppError } = require('./AppError')

function errorHandler(error, request, reply) {
  if (error.validation) {
    return reply.status(422).send({
      error: 'VALIDATION_ERROR',
      message: 'Invalid request data',
      details: error.validation,
    })
  }

  if (error instanceof AppError) {
    return reply.status(error.statusCode).send({
      error: error.code,
      message: error.message,
    })
  }

  request.log.error({ err: error }, 'Unhandled error')

  return reply.status(500).send({
    error: 'INTERNAL_ERROR',
    message: 'An unexpected error occurred',
  })
}

module.exports = errorHandler
