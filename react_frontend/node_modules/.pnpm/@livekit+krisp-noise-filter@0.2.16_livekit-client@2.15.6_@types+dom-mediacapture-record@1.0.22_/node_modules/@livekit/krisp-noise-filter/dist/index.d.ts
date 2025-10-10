import { KrispNoiseFilterProcessor, type NoiseFilterOptions } from "./NoiseFilterProcessor";
declare const isKrispNoiseFilterSupported: typeof KrispNoiseFilterProcessor.isSupported;
declare const KrispNoiseFilter: (options?: NoiseFilterOptions) => KrispNoiseFilterProcessor;
export { isKrispNoiseFilterSupported, KrispNoiseFilter, NoiseFilterOptions, type KrispNoiseFilterProcessor, };
