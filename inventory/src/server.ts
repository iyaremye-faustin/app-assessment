import Fastify from 'fastify'

interface Product {
  id: string
  name: string
  stock: number
}

const fastify = Fastify({ logger: true })

let products: Product[] = [
  { id: '1', name: 'Inkweto', stock: 15 },
  { id: '2', name: 'Ibikapu', stock: 50 },
  { id: '3', name: 'Imipira', stock: 30 },
  {
    id: '4', name: 'Jeans', stock: 22
  },
  { id: '5', name: 'Lacoste', stock: 10 },
  { id: '6', name: 'Imikandara', stock: 9 },
  { id: '7', name: 'Socks', stock: 19 },
  { id: '8', name: 'Imisego', stock: 28 },
  { id: '9', name: 'Raclette', stock: 47 },
  { id: '10', name: 'Isaha', stock: 98 },
]

// GET all products
fastify.get('/products', async (request, reply) => {
  return products
})

// GET single product
fastify.get<{ Params: { id: string } }>('/products/:id', async (request, reply) => {
  const product = products.find(p => p.id === request.params.id)
  if (!product) {
    return reply.code(404).send({ error: 'Product not found' })
  }
  return product
})

// Add new product
fastify.post<{ Body: Omit<Product, 'id'> }>('/products', async (request, reply) => {
  const newProduct: Product = {
    id: String(Math.max(...products.map(p => parseInt(p.id)), 0) + 1),
    ...request.body
  }
  products.push(newProduct)
  return reply.code(201).send(newProduct)
})


const start = async () => {
  try {
    const port = Number(process.env.PORT ?? 8082)
    await fastify.listen({ port, host: '0.0.0.0' })
    console.log(`Server running on http://localhost:${port}`)
  } catch (err) {
    fastify.log.error(err)
    process.exit(1)
  }
}

start()
