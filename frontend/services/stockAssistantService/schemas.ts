import * as z from "zod"

export const signInFormSchema = z.object({
  email: z.email({ error: "Provide email address" }),
  password: z.string(),
})

export const signUpFormSchema = z
  .object({
    name: z.string().min(2, "Name must contain at least 2 characters").max(64, "Name can contain a maximum a maximum of 64 characters"),
    email: z.email({ error: "Provide email address" }),
    password: z.string().min(8, "password must contain at least 8 characters").max(64, "password can't has more than 64 characters").regex(/\d/, "password must contain one number"),
    passwordRepeat: z.string(),
  })
  .refine(({ password, passwordRepeat }) => password === passwordRepeat, {
    message: "Passwords do not match",
    path: ["passwordRepeat"],
  })

export const MAX_CHAT_MESSAGE_LENGTH = 300

export const chatRequestFormSchema = z.object({
  message: z.string().trim().min(1, "message must have some text").max(MAX_CHAT_MESSAGE_LENGTH, `message can have at most ${MAX_CHAT_MESSAGE_LENGTH} characters`),
  conversationId: z.uuid(),
  newConversation: z.boolean().optional(),
})

export type SignInFormType = z.infer<typeof signInFormSchema>
export type SignUpFormType = z.infer<typeof signUpFormSchema>
export type chatRequestSchemaType = z.infer<typeof chatRequestFormSchema>
