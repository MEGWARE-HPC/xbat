import { defineCollection, defineContentConfig } from '@nuxt/content'

export default defineContentConfig({
  collections: {
    docs: defineCollection({
      source: {
        include: 'docs/**/*.md'
      },
      type: 'page',
      schema: {
        title: {
          type: 'string',
          required: true
        },
        description: {
          type: 'string'
        },
        date: {
          type: 'date'
        },
        draft: {
          type: 'boolean',
          default: false
        }
      }
    })
  }
})
