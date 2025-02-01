import React from 'react';
import { AgentStep } from '../../types/agent';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/solid';

interface AgentProgressProps {
    steps: AgentStep[];
    isLoading?: boolean;
}

export const AgentProgress: React.FC<AgentProgressProps> = ({ steps, isLoading }) => {
    return (
        <div className="flex flex-col space-y-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <h3 className="text-lg font-semibold">Agent Progress</h3>
            <div className="space-y-4">
                {steps.map((step, index) => (
                    <AgentStepCard key={index} step={step} />
                ))}
                {isLoading && (
                    <div className="flex items-center space-x-2 text-gray-500">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
                        <span>Agent is thinking...</span>
                    </div>
                )}
            </div>
        </div>
    );
};

interface AgentStepCardProps {
    step: AgentStep;
}

const AgentStepCard: React.FC<AgentStepCardProps> = ({ step }) => {
    const hasError = !!step.error;
    
    return (
        <div className={`border rounded-lg p-4 ${hasError ? 'border-red-300 bg-red-50' : 'border-gray-200 bg-white'} dark:border-gray-700 dark:bg-gray-900`}>
            <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                    {hasError ? (
                        <XCircleIcon className="h-5 w-5 text-red-500" />
                    ) : (
                        <CheckCircleIcon className="h-5 w-5 text-green-500" />
                    )}
                    <span className="font-medium">Step {step.step_number}</span>
                </div>
                <span className="text-sm text-gray-500">
                    {step.duration.toFixed(2)}s
                </span>
            </div>
            
            {step.tool_calls?.map((tool, index) => (
                <div key={index} className="mt-2 space-y-1">
                    <div className="text-sm font-medium">Tool: {tool.name}</div>
                    <pre className="text-xs bg-gray-50 dark:bg-gray-800 p-2 rounded">
                        {JSON.stringify(tool.arguments, null, 2)}
                    </pre>
                </div>
            ))}
            
            {step.observations && (
                <div className="mt-2 space-y-1">
                    <div className="text-sm font-medium">Observations:</div>
                    <div className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
                        {step.observations}
                    </div>
                </div>
            )}
            
            {step.error && (
                <div className="mt-2 text-sm text-red-600 dark:text-red-400">
                    Error: {step.error}
                </div>
            )}
            
            {step.action_output && (
                <div className="mt-2 space-y-1">
                    <div className="text-sm font-medium">Output:</div>
                    <div className="text-sm text-gray-600 dark:text-gray-300">
                        {step.action_output}
                    </div>
                </div>
            )}
        </div>
    );
}; 