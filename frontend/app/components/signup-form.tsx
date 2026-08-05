import { cn } from "~/lib/utils"
import { Card, CardContent } from "~/components/ui/card"
import { Input } from "~/components/ui/input"
import { Label } from "~/components/ui/label"
import { type UserType } from "~/contexts/AuthContext"
import { Link, useNavigate } from "react-router"
import api from "~/lib/api"
import { toast } from "sonner"
import type { AxiosError } from "axios"
import { SubmitButton } from "~/components/ui/submit-button"

export function SignupForm({
  className,
  user,
  ...props
}: { user: UserType } & React.ComponentProps<"div">) {
  const navigate = useNavigate()

  async function signupUser(data: FormData) {
    const name = data.get("name")?.toString()
    const email = data.get("email")?.toString()
    const password = data.get("password")?.toString()

    if (!name || !email || !password) {
      return
    }

    try {
      if (user === "seller") {
        const address = data.get("address")?.toString()
        const zip_code = data.get("zip_code")?.toString()

        if (!address || !zip_code) {
          return
        }

        await api.seller.registerSeller({
          name,
          email,
          password,
          address,
          zip_code: Number(zip_code),
        })
      } else {
        const max_handling_capacity = data.get("max_handling_capacity")?.toString()
        const serviceable_zip_codes_raw = data.get("serviceable_zip_codes")?.toString()

        if (!max_handling_capacity || !serviceable_zip_codes_raw) {
          return
        }

        const serviceable_zip_codes = serviceable_zip_codes_raw
          .split(",")
          .map((code) => code.trim())
          .filter(Boolean)
          .map(Number)

        if (serviceable_zip_codes.length === 0 || serviceable_zip_codes.some(Number.isNaN)) {
          toast.error("Please enter valid zip codes separated by commas.")
          return
        }

        await api.partner.registerDeliveryPartner({
          name,
          email,
          password,
          max_handling_capacity: Number(max_handling_capacity),
          serviceable_zip_codes,
        })
      }

      toast.success(
        "Account created successfully. Please verify your email before logging in."
      )
      navigate(`/${user}/login`)
    } catch (error) {
      const apiError = error as AxiosError<{ detail?: string | { msg: string }[] }>
      const detail = apiError.response?.data?.detail

      if (typeof detail === "string") {
        toast.error(detail)
      } else if (Array.isArray(detail) && detail.length > 0) {
        toast.error(detail[0].msg)
      } else {
        toast.error("Signup failed. Please check your details and try again.")
      }
    }
  }

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="overflow-hidden p-0">
        <CardContent className="grid p-0 md:grid-cols-2">
          <form className="p-6 md:p-8" action={signupUser}>
            <div className="flex flex-col gap-6">
              <div className="flex flex-col items-center text-center">
                <h1 className="text-2xl font-bold">Create an account</h1>
                <p className="text-muted-foreground text-balance">
                  Sign up for your FastShip account
                </p>
              </div>
              <div className="grid gap-3">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  type="text"
                  name="name"
                  placeholder="John Doe"
                  required
                />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  name="email"
                  placeholder="m@example.com"
                  required
                />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" name="password" required />
              </div>
              {user === "seller" ? (
                <>
                  <div className="grid gap-3">
                    <Label htmlFor="address">Address</Label>
                    <Input
                      id="address"
                      type="text"
                      name="address"
                      placeholder="123 Main St"
                      required
                    />
                  </div>
                  <div className="grid gap-3">
                    <Label htmlFor="zip_code">Zip Code</Label>
                    <Input
                      id="zip_code"
                      type="number"
                      name="zip_code"
                      placeholder="12345"
                      required
                    />
                  </div>
                </>
              ) : (
                <>
                  <div className="grid gap-3">
                    <Label htmlFor="serviceable_zip_codes">Serviceable Zip Codes</Label>
                    <Input
                      id="serviceable_zip_codes"
                      type="text"
                      name="serviceable_zip_codes"
                      placeholder="11001, 11002, 11003"
                      required
                    />
                  </div>
                  <div className="grid gap-3">
                    <Label htmlFor="max_handling_capacity">Max Handling Capacity</Label>
                    <Input
                      id="max_handling_capacity"
                      type="number"
                      name="max_handling_capacity"
                      placeholder="10"
                      min={1}
                      required
                    />
                  </div>
                </>
              )}
              <SubmitButton text="Sign up" />
              <div className="text-center text-sm">
                Already have an account?{" "}
                <Link to={`/${user}/login`} className="underline underline-offset-4">
                  Login
                </Link>
              </div>
            </div>
          </form>
          <div className="bg-muted relative hidden md:block">
            <img
              src="/delivery_boy_pic.jpg"
              alt="Image"
              className="absolute inset-0 h-full w-full object-cover dark:brightness-[0.2] dark:grayscale"
            />
          </div>
        </CardContent>
      </Card>
      <div className="text-muted-foreground *:[a]:hover:text-primary text-center text-xs text-balance *:[a]:underline *:[a]:underline-offset-4">
        By clicking continue, you agree to our <a href="#">Terms of Service</a>{" "}
        and <a href="#">Privacy Policy</a>.
      </div>
    </div>
  )
}
