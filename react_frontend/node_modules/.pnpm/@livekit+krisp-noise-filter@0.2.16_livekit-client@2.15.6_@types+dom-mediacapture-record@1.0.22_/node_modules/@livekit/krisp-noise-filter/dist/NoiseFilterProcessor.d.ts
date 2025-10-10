import { Track } from "livekit-client";
import type { AudioProcessorOptions, Room, TrackProcessor } from "livekit-client";
import { KrispOptions } from "./options";
export type NoiseFilterOptions = KrispOptions;
export declare class KrispNoiseFilterProcessor implements TrackProcessor<Track.Kind.Audio, AudioProcessorOptions> {
    #private;
    readonly name = "livekit-noise-filter";
    processedTrack?: MediaStreamTrack | undefined;
    private trackSettings?;
    private originalTrack?;
    constructor(options?: NoiseFilterOptions);
    static isSupported(): boolean;
    /**
     * @internal
     */
    init: (opts: AudioProcessorOptions) => Promise<void>;
    restart: (opts: AudioProcessorOptions) => Promise<void>;
    onPublish(room: Room): Promise<void>;
    setEnabled(enable: boolean): Promise<boolean | undefined>;
    isEnabled(): boolean;
    destroy: () => Promise<void>;
}
