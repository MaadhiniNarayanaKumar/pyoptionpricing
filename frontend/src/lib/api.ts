const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export type OptionType = "call" | "put";
export type Model = "black_scholes" | "binomial" | "monte_carlo" | "asian" | "barrier";
export type Style = "european" | "american";
export type BarrierType = "up-and-out" | "up-and-in" | "down-and-out" | "down-and-in";

export interface MarketInputs {
  spot: number;
  strike: number;
  maturity: number;
  rate: number;
  option_type: OptionType;
  model: Model;
  style: Style;
  steps?: number;
  n_paths?: number;
  n_steps?: number;
  seed?: number;
  barrier?: number;
  barrier_type?: BarrierType;
}

export interface OptionRequest extends MarketInputs {
  volatility: number;
}

export interface Greeks {
  delta: number;
  gamma: number;
  vega: number;
  theta: number;
  rho: number;
}

export interface PriceResponse {
  model: string;
  style: string;
  price: number;
  standard_error?: number;
}

export interface GreeksResponse {
  model: string;
  style: string;
  greeks: Greeks;
}

export interface CompareResult {
  model: string;
  style: string;
  class: string;
  price: number;
  greeks: Greeks;
  standard_error?: number;
}

export interface ConvergenceResponse {
  binomial: { black_scholes: number; points: { steps: number; price: number }[] };
  monte_carlo: {
    black_scholes: number;
    points: { n_paths: number; price: number; standard_error: number }[];
  };
}

export interface PayoffResponse {
  premium: number;
  strike: number;
  points: { spot: number; payoff: number; profit: number }[];
}

export interface PathsResponse {
  times: number[];
  paths: number[][];
  strike: number;
  barrier: number | null;
}

export interface ImpliedVolResponse {
  implied_vol: number;
  market_price: number;
  model: string;
}

export interface SmilePoint {
  strike: number;
  market_price: number;
  implied_vol: number;
}

export interface VolSurfaceRequest {
  spot: number;
  rate: number;
  option_type: OptionType;
  atm_vol: number;
  skew: number;
  strikes?: number[];
  maturities?: number[];
}

export interface VolSurfaceResponse {
  strikes: number[];
  surface: { maturity: number; smile: SmilePoint[] }[];
}

/** An API failure. fieldErrors maps request fields to messages from validation. */
export class ApiError extends Error {
  constructor(message: string, public fieldErrors: Record<string, string> = {}) {
    super(message);
  }
}

interface ValidationIssue {
  loc: (string | number)[];
  msg: string;
}

async function post<T>(path: string, body: object): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError(`Cannot reach the API at ${API_URL}. Is the backend running?`);
  }

  const data = await response.json().catch(() => null);
  if (response.ok) return data as T;

  const detail = data?.detail;
  if (Array.isArray(detail)) {
    const fieldErrors: Record<string, string> = {};
    for (const issue of detail as ValidationIssue[]) {
      const field = String(issue.loc[issue.loc.length - 1]);
      fieldErrors[field] = issue.msg;
    }
    throw new ApiError("Some inputs are invalid.", fieldErrors);
  }
  throw new ApiError(typeof detail === "string" ? detail : `Request failed (${response.status}).`);
}

export const getPrice = (req: OptionRequest) => post<PriceResponse>("/price", req);
export const getGreeks = (req: OptionRequest) => post<GreeksResponse>("/greeks", req);
export const compareModels = (req: OptionRequest) =>
  post<{ results: CompareResult[] }>("/compare", req);
export const getConvergence = (req: OptionRequest) =>
  post<ConvergenceResponse>("/convergence", req);
export const getPayoff = (req: OptionRequest) => post<PayoffResponse>("/payoff", req);
export const getPaths = (req: OptionRequest & { n_display?: number }) =>
  post<PathsResponse>("/paths", req);
export const getImpliedVol = (req: MarketInputs & { market_price: number }) =>
  post<ImpliedVolResponse>("/implied-vol", req);
export const getVolSurface = (req: VolSurfaceRequest) =>
  post<VolSurfaceResponse>("/vol-surface", req);
