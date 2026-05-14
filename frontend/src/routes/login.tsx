import { Button, Form, PasswordInput, Stack, TextInput } from "@carbon/react";
import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { type SubmitHandler, useForm } from "react-hook-form";

import { Logo } from "@/components/common/Logo";
import type { BodyLoginLoginAccessToken as AccessToken } from "../client";
import useAuth, { isLoggedIn } from "../hooks/useAuth";
import { emailPattern } from "../utils";

export const Route = createFileRoute("/login")({
  component: Login,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      });
    }
  },
});

function Login() {
  const { loginMutation, error, resetError } = useAuth();
  const form = useForm({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      username: "",
      password: "",
    },
  });

  const onSubmit: SubmitHandler<AccessToken> = async (data) => {
    resetError();

    try {
      await loginMutation.mutateAsync(data);
    } catch {
      // error is handled by useAuth hook
    }
  };

  return (
    <div className="flex min-h-[100dvh] flex-col lg:flex-row">
      {/* Left side - Login Form */}
      <div className="flex flex-1 flex-col justify-center p-4 lg:p-8">
        <div className="mx-auto w-full max-w-sm">
          <Form onSubmit={form.handleSubmit(onSubmit)}>
            <Stack gap={5}>
              <Logo className="mb-2 w-full" />
              <TextInput
                id="username"
                labelText="Email"
                placeholder="Email"
                invalid={!!form.formState.errors.username}
                invalidText={form.formState.errors.username?.message}
                {...form.register("username", {
                  required: "Username is required",
                  pattern: emailPattern,
                })}
              />
              <PasswordInput
                id="password"
                placeholder="Password"
                labelText="Password"
                hidePasswordLabel="Hide password"
                showPasswordLabel="Show password"
                invalid={!!form.formState.errors.password || !!error}
                invalidText={form.formState.errors.password?.message || error}
                {...form.register("password", {
                  required: "Password is required",
                })}
              />{" "}
              <Button type="submit" className="mt-4 w-full max-w-full">
                {form.formState.isSubmitting ? "Loading..." : "Log In"}
              </Button>
              <div className="flex w-full justify-center gap-2">
                Don't have an account? <Link to="/signup">Sign up</Link>
              </div>
            </Stack>
          </Form>
        </div>
      </div>

      {/* Right side - STT-WXO Demo (Public, No Auth Required) */}
      <div className="hidden flex-1 border-l border-cds-border-subtle lg:flex">
        <iframe
          src="https://stt-demo-git-sst-demo.walaris-poc-cluster-e283fb2d1444b49f5790a495dd0d982a-0000.eu-de.containers.appdomain.cloud/public/stt-wxo"
          className="h-full w-full border-0"
          title="STT-WXO Demo"
          allow="microphone"
        />
      </div>
    </div>
  );
}
