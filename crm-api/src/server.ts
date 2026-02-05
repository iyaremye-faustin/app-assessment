import Fastify, { type FastifyInstance } from 'fastify'

interface Customer {
  id: number
  name: string
  email: string
  phone?: string
  productIds: string[]
}

type CustomerInput = Omit<Customer, 'id'>

const fastify: FastifyInstance = Fastify({ logger: true })

const ALL_PRODUCT_IDS = ['1', '2', '3', '4', '5', '6'] as const
const INITIAL_CUSTOMERS_COUNT = 10

const toInt = (value: string) => Number.parseInt(value, 10)

const nextId = (rows: Customer[]) =>
  rows.length ? Math.max(...rows.map((c) => c.id)) + 1 : 1

const seedCustomers = (count: number): Customer[] =>
  Array.from({ length: count }, (_, i) => {
    const id = i + 1

    const primaryProduct = ALL_PRODUCT_IDS[i % ALL_PRODUCT_IDS.length]!
    const secondaryProduct = ALL_PRODUCT_IDS[(i + 1) % ALL_PRODUCT_IDS.length]!

    const productIds = id % 2 === 0 ? [primaryProduct, secondaryProduct] : [primaryProduct]

    return {
      id,
      name: `Customer ${id}`,
      email: `customer${id}@example.com`,
      phone: `0788${String(id).padStart(2, '0')}`,
      productIds,
    }
  })

let customers: Customer[] = seedCustomers(INITIAL_CUSTOMERS_COUNT)

// GET all customers
fastify.get('/customers', async () => customers)

// GET single customer
fastify.get<{ Params: { id: string } }>('/customers/:id', async (request, reply) => {
  const id = toInt(request.params.id)
  const customer = customers.find((c) => c.id === id)

  if (!customer) return reply.code(404).send({ error: 'Customer not found' })

  return customer
})

// Add new customer
fastify.post<{ Body: CustomerInput }>('/customers', async (request, reply) => {
  const newCustomer: Customer = {
    id: nextId(customers),
    ...request.body,
  }

  customers.push(newCustomer)
  return reply.code(201).send(newCustomer)
})

const start = async () => {
  const port = Number(process.env.PORT ?? 8081)

  try {
    await fastify.listen({ port, host: '0.0.0.0' })
    fastify.log.info(`Server running on http://localhost:${port}`)
  } catch (err) {
    fastify.log.error(err)
    process.exit(1)
  }
}

void start()
