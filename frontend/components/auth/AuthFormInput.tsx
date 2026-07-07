"use client"

import { SignUpFormType } from "@/services/stockAssistantService/schemas"
import { useFormContext, FieldPath } from "react-hook-form"

type AuthFormFieldProps = {
  label: string
  inputType?: string
  autoComplete?: string
  name: FieldPath<SignUpFormType>
}

const AuthFormField = ({ label, inputType = "text", autoComplete, name }: AuthFormFieldProps) => {
  const { register, formState } = useFormContext<SignUpFormType>()
  const error = formState.errors[name]

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-col gap-1">
        <label htmlFor={label} className="text-sm font-medium capitalize ">
          {label}
        </label>
        <input id={label} {...register(name)} type={inputType} autoComplete={autoComplete} className="rounded border border-neutral-300 px-3 py-2" />
      </div>
      {error
        ? (
            <p className="text-sm text-red-600" role="alert">
              {error.message}
            </p>
          )
        : null}
    </div>
  )
}

export default AuthFormField
