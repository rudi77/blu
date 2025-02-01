export interface AgentStep {
    step_number: number;
    start_time: number;
    end_time: number;
    duration: number;
    tool_calls?: {
        name: string;
        arguments: Record<string, any>;
        id: string;
    }[];
    observations?: string;
    error?: string;
    action_output?: string;
    model_output?: string;
}

export interface AgentResponse {
    response: string;
    logs: AgentStep[];
}

export interface AgentWebSocketMessage {
    type: 'step_update' | 'error';
    step?: AgentStep;
    detail?: string;
}

export interface AgentMessage {
    type: 'message' | 'error' | 'status';
    content: string;
    metadata?: {
        step?: number;
        total_steps?: number;
        tool?: string;
    };
} 