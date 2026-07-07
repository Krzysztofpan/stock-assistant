"use client"

import Link from "next/link"
import { startTransition, useActionState } from "react"

import { signUp } from "@/services/stockAssistantService/auth-actions"
import AuthFormField from "@/components/auth/AuthFormInput"
import { FormProvider, useForm } from "react-hook-form"
import { signUpFormSchema, SignUpFormType } from "@/services/stockAssistantService/schemas"
import { zodResolver } from "@hookform/resolvers/zod"

export function SignUpForm() {
  const [state, formAction, isPending] = useActionState(signUp, {})
  const form = useForm<SignUpFormType>({
    resolver: zodResolver(signUpFormSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  })

  const onSubmit = (data: SignUpFormType) => {
    const formData = new FormData()

    formData.set("name", data.name)
    formData.set("email", data.email)
    formData.set("password", data.password)
    formData.set("passwordRepeat", data.passwordRepeat)

    startTransition(() => {
      formAction(formData)
    })
  }

  return (
    <FormProvider {...form}>
      <form action={formAction} onSubmit={form.handleSubmit(onSubmit)} className="flex w-full max-w-sm flex-col gap-4 md:gap-6">
        <AuthFormField name="name" label="name" autoComplete="name" />
        <AuthFormField name="email" label="email" autoComplete="email" />
        <AuthFormField name="password" inputType="password" label="password" autoComplete="current-password" />
        <AuthFormField name="passwordRepeat" inputType="password" label="repeat password" autoComplete="current-password_repeat" />

        {state.error
          ? (
              <p className="text-sm text-red-600" role="alert">
                {state.error}
              </p>
            )
          : null}

        <button
          type="submit"
          disabled={isPending}
          className="rounded bg-neutral-900 px-4 py-2 text-white disabled:opacity-50"
        >
          {isPending ? "Creating account..." : "Sign up"}
        </button>

        <p className="text-sm text-neutral-600 text-center">
          Already have an account?
          {" "}
          <Link href="/auth/sign-in" className="underline">
            Sign in
          </Link>
        </p>
      </form>
    </FormProvider>
  )
}
