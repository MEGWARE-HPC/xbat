import { defineCollection, defineContentConfig, z } from "@nuxt/content";

export default defineContentConfig({
    collections: {
        docs: defineCollection({
            source: {
                include: "docs/**/*"
            },
            type: "page",
            schema: z.object({
                title: z.string().min(1),
                description: z.string().optional(),
                date: z.string().optional(),
                draft: z.boolean().default(false)
            })
        })
    }
});
