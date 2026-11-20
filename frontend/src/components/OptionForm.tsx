"use client";

import type { BarrierType, Model, OptionRequest, OptionType, Style } from "@/lib/api";

export interface FormValues {
  spot: string;
  strike: string;
  maturity: string;
  ratePct: string;
  volPct: string;
  option_type: OptionType;
  model: Model;
  style: Style;
  steps: string;
  n_paths: string;
  n_steps: string;
  seed: string;
  barrier: string;
  barrier_type: BarrierType;
}

export const DEFAULT_VALUES: FormValues = {
  spot: "100",
  strike: "100",
  maturity: "1",
  ratePct: "5",
  volPct: "20",
  option_type: "call",
  model: "black_scholes",
  style: "european",
  steps: "200",
  n_paths: "50000",
  n_steps: "50",
  seed: "42",
  barrier: "120",
  barrier_type: "up-and-out",
};

const SIMULATED: Model[] = ["monte_carlo", "asian", "barrier"];

/** Form errors use the API's field names, so server and client errors share one map. */
export type FieldErrors = Record<string, string>;

export function toRequest(v: FormValues): { request?: OptionRequest; errors: FieldErrors } {
  const errors: FieldErrors = {};
  const num = (raw: string, field: string) => {
    const value = Number(raw);
    if (raw.trim() === "" || !Number.isFinite(value)) errors[field] = "Enter a number.";
    return value;
  };

  const request: OptionRequest = {
    spot: num(v.spot, "spot"),
    strike: num(v.strike, "strike"),
    maturity: num(v.maturity, "maturity"),
    rate: num(v.ratePct, "rate") / 100,
    volatility: num(v.volPct, "volatility") / 100,
    option_type: v.option_type,
    model: v.model,
    style: v.model === "binomial" ? v.style : "european",
  };
  if (v.model === "binomial") request.steps = num(v.steps, "steps");
  if (SIMULATED.includes(v.model)) {
    request.n_paths = num(v.n_paths, "n_paths");
    request.seed = num(v.seed, "seed");
  }
  if (v.model === "asian" || v.model === "barrier") request.n_steps = num(v.n_steps, "n_steps");
  if (v.model === "barrier") {
    request.barrier = num(v.barrier, "barrier");
    request.barrier_type = v.barrier_type;
  }
  return Object.keys(errors).length ? { errors } : { request, errors };
}

interface Props {
  values: FormValues;
  onChange: (values: FormValues) => void;
  onSubmit: () => void;
  fieldErrors: FieldErrors;
  formError: string | null;
  loading: boolean;
}

export default function OptionForm({ values, onChange, onSubmit, fieldErrors, formError, loading }: Props) {
  const set = <K extends keyof FormValues>(key: K, value: FormValues[K]) =>
    onChange({ ...values, [key]: value });

  const numberField = (key: keyof FormValues, label: string, errorKey: string, hint?: string) => (
    <Field label={label} error={fieldErrors[errorKey]} hint={hint}>
      <input
        type="number"
        step="any"
        value={values[key]}
        onChange={(e) => set(key, e.target.value as never)}
        className={inputClass(!!fieldErrors[errorKey])}
      />
    </Field>
  );

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
      className="space-y-4"
    >
      <div className="grid grid-cols-2 gap-3">
        {numberField("spot", "Spot (S)", "spot")}
        {numberField("strike", "Strike (K)", "strike")}
        {numberField("maturity", "Maturity (years)", "maturity")}
        {numberField("ratePct", "Rate (%)", "rate")}
        {numberField("volPct", "Volatility (%)", "volatility")}
        <Field label="Type">
          <select
            value={values.option_type}
            onChange={(e) => set("option_type", e.target.value as OptionType)}
            className={inputClass(false)}
          >
            <option value="call">Call</option>
            <option value="put">Put</option>
          </select>
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Field label="Model" error={fieldErrors.model}>
          <select
            value={values.model}
            onChange={(e) => set("model", e.target.value as Model)}
            className={inputClass(false)}
          >
            <option value="black_scholes">Black-Scholes</option>
            <option value="binomial">Binomial (CRR)</option>
            <option value="monte_carlo">Monte Carlo</option>
            <option value="asian">Asian (MC)</option>
            <option value="barrier">Barrier (MC)</option>
          </select>
        </Field>
        <Field label="Exercise" error={fieldErrors.style}>
          <select
            value={values.model === "binomial" ? values.style : "european"}
            disabled={values.model !== "binomial"}
            onChange={(e) => set("style", e.target.value as Style)}
            className={inputClass(false)}
          >
            <option value="european">European</option>
            <option value="american">American</option>
          </select>
        </Field>
      </div>

      {values.model !== "black_scholes" && (
        <div className="grid grid-cols-2 gap-3 rounded-md bg-slate-50 p-3">
          {values.model === "binomial" && numberField("steps", "Tree steps", "steps")}
          {SIMULATED.includes(values.model) && numberField("n_paths", "Paths", "n_paths")}
          {(values.model === "asian" || values.model === "barrier") &&
            numberField("n_steps", "Time steps", "n_steps")}
          {SIMULATED.includes(values.model) && numberField("seed", "Seed", "seed")}
          {values.model === "barrier" && numberField("barrier", "Barrier level", "barrier")}
          {values.model === "barrier" && (
            <Field label="Barrier type" error={fieldErrors.barrier_type}>
              <select
                value={values.barrier_type}
                onChange={(e) => set("barrier_type", e.target.value as BarrierType)}
                className={inputClass(false)}
              >
                <option value="up-and-out">Up-and-out</option>
                <option value="up-and-in">Up-and-in</option>
                <option value="down-and-out">Down-and-out</option>
                <option value="down-and-in">Down-and-in</option>
              </select>
            </Field>
          )}
        </div>
      )}

      {formError && (
        <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {formError}
        </p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-60"
      >
        {loading ? "Pricing…" : "Price option"}
      </button>
    </form>
  );
}

function Field({ label, error, hint, children }: {
  label: string;
  error?: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium text-slate-700">{label}</span>
      {children}
      {error ? (
        <span className="mt-1 block text-xs text-red-600">{error}</span>
      ) : hint ? (
        <span className="mt-1 block text-xs text-slate-500">{hint}</span>
      ) : null}
    </label>
  );
}

const inputClass = (invalid: boolean) =>
  `w-full rounded-md border px-2 py-1.5 text-sm bg-white disabled:bg-slate-100 disabled:text-slate-500 ${
    invalid ? "border-red-400 focus:outline-red-500" : "border-slate-300 focus:outline-blue-500"
  }`;
