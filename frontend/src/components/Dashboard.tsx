"use client";

import Image from "next/image";
import { useState } from "react";
import { getGreeks, getPrice, type OptionRequest } from "@/lib/api";
import { useRequest } from "@/lib/useRequest";
import CompareView from "./CompareView";
import ConvergenceChart from "./ConvergenceChart";
import OptionForm, { DEFAULT_VALUES, toRequest, type FieldErrors, type FormValues } from "./OptionForm";
import PathsChart from "./PathsChart";
import PayoffChart from "./PayoffChart";
import PriceCards from "./PriceCards";
import SmileChart from "./SmileChart";

const TABS = [
  { id: "compare", label: "Compare models" },
  { id: "payoff", label: "Payoff" },
  { id: "convergence", label: "Convergence" },
  { id: "paths", label: "Paths" },
  { id: "smile", label: "IV smile" },
] as const;
type TabId = (typeof TABS)[number]["id"];

export default function Dashboard() {
  const [values, setValues] = useState<FormValues>(DEFAULT_VALUES);
  const [submitted, setSubmitted] = useState<OptionRequest>(() => toRequest(DEFAULT_VALUES).request!);
  const [localErrors, setLocalErrors] = useState<FieldErrors>({});
  const [tab, setTab] = useState<TabId>("compare");

  const key = JSON.stringify(submitted);
  const priced = useRequest(key, () => Promise.all([getPrice(submitted), getGreeks(submitted)]));

  // Server errors describe the last submitted request, so hide them once local checks fail.
  const hasLocalErrors = Object.keys(localErrors).length > 0;
  const fieldErrors = hasLocalErrors ? localErrors : priced.fieldErrors;
  const formError =
    hasLocalErrors || Object.keys(priced.fieldErrors).length > 0
      ? "Fix the highlighted inputs."
      : priced.error ?? null;
  const shown = priced.data ?? priced.lastData;

  const submit = () => {
    const { request, errors } = toRequest(values);
    setLocalErrors(errors);
    if (request) setSubmitted(request);
  };

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6">
      <header className="mb-6 flex items-center gap-3">
        <Image src="/logo.png" alt="pyoptionpricing logo" width={44} height={44} priority className="h-11 w-11" />
        <div>
          <h1 className="text-2xl font-bold text-slate-900">pyoptionpricing</h1>
          <p className="text-sm text-slate-600">
            Price European, American and path-dependent options with Black-Scholes, a binomial tree and Monte Carlo.
          </p>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <aside className="h-fit rounded-lg border border-slate-200 bg-white p-4 shadow-sm lg:sticky lg:top-6">
          <OptionForm
            values={values}
            onChange={setValues}
            onSubmit={submit}
            fieldErrors={fieldErrors}
            formError={formError}
            loading={priced.loading}
          />
        </aside>

        <main className="min-w-0 space-y-6">
          {shown ? (
            <div className={priced.loading || priced.error ? "opacity-60 transition-opacity" : "transition-opacity"}>
              <PriceCards price={shown[0]} greeks={shown[1]} />
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
              {priced.loading ? "Pricing…" : "Price an option to see results."}
            </div>
          )}

          {shown && !priced.error && (
            <>
              <nav className="flex flex-wrap gap-1 border-b border-slate-200">
                {TABS.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setTab(t.id)}
                    className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${
                      tab === t.id
                        ? "border-blue-600 text-blue-700"
                        : "border-transparent text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </nav>

              {tab === "compare" && <CompareView request={submitted} />}
              {tab === "payoff" && <PayoffChart request={submitted} />}
              {tab === "convergence" && <ConvergenceChart request={submitted} />}
              {tab === "paths" && <PathsChart request={submitted} />}
              {tab === "smile" && <SmileChart request={submitted} />}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
