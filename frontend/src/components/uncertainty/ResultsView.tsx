import { useQuery } from "@tanstack/react-query";
import { Loading, Tile, ProgressBar, InlineNotification } from "@carbon/react";
import { CheckmarkFilled, ErrorFilled, InProgress } from "@carbon/icons-react";

interface ResultsViewProps {
  experimentId: string;
}

export default function ResultsView({ experimentId }: ResultsViewProps) {
  const { data: experiment, isLoading, refetch } = useQuery({
    queryKey: ["experiment", experimentId],
    queryFn: async () => {
      const response = await fetch(`/api/v1/experiments/${experimentId}`);
      if (!response.ok) throw new Error("Failed to fetch experiment");
      return response.json();
    },
    refetchInterval: (data) => {
      // Refetch every 2 seconds if running
      return data?.status === "running" ? 2000 : false;
    },
  });

  if (isLoading) {
    return <Loading description="Loading experiment results..." />;
  }

  if (!experiment) {
    return <div>Experiment not found</div>;
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckmarkFilled className="text-green-600" size={24} />;
      case "failed":
        return <ErrorFilled className="text-red-600" size={24} />;
      case "running":
        return <InProgress className="text-blue-600" size={24} />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "text-green-600";
      case "failed":
        return "text-red-600";
      case "running":
        return "text-blue-600";
      default:
        return "text-gray-600";
    }
  };

  return (
    <div className="py-6">
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          {getStatusIcon(experiment.status)}
          <div>
            <h2 className="text-2xl font-semibold">{experiment.name}</h2>
            <p className={`text-lg ${getStatusColor(experiment.status)}`}>
              Status: {experiment.status.toUpperCase()}
            </p>
          </div>
        </div>

        {experiment.status === "running" && (
          <div className="mb-6">
            <ProgressBar
              label="Training Progress"
              value={experiment.progress * 100}
              max={100}
            />
            <p className="text-sm text-gray-600 mt-2">
              Progress: {(experiment.progress * 100).toFixed(1)}%
            </p>
          </div>
        )}

        {experiment.status === "failed" && experiment.error_message && (
          <InlineNotification
            kind="error"
            title="Experiment Failed"
            subtitle={experiment.error_message}
            className="mb-6"
          />
        )}
      </div>

      {experiment.status === "completed" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Tile>
            <h3 className="text-lg font-semibold mb-2">Aleatoric Uncertainty Detection</h3>
            <p className="text-4xl font-bold text-blue-600">
              {experiment.aleatoric_auroc 
                ? (experiment.aleatoric_auroc * 100).toFixed(1) + "%" 
                : "N/A"}
            </p>
            <p className="text-sm text-gray-600 mt-2">AUROC Score</p>
          </Tile>

          <Tile>
            <h3 className="text-lg font-semibold mb-2">Epistemic Uncertainty Detection</h3>
            <p className="text-4xl font-bold text-purple-600">
              {experiment.epistemic_auroc 
                ? (experiment.epistemic_auroc * 100).toFixed(1) + "%" 
                : "N/A"}
            </p>
            <p className="text-sm text-gray-600 mt-2">AUROC Score</p>
          </Tile>
        </div>
      )}

      <div className="mt-8">
        <Tile>
          <h3 className="text-lg font-semibold mb-4">Experiment Details</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600">Created:</p>
              <p className="font-semibold">{new Date(experiment.created_at).toLocaleString()}</p>
            </div>
            {experiment.started_at && (
              <div>
                <p className="text-gray-600">Started:</p>
                <p className="font-semibold">{new Date(experiment.started_at).toLocaleString()}</p>
              </div>
            )}
            {experiment.completed_at && (
              <div>
                <p className="text-gray-600">Completed:</p>
                <p className="font-semibold">{new Date(experiment.completed_at).toLocaleString()}</p>
              </div>
            )}
            {experiment.results_path && (
              <div>
                <p className="text-gray-600">Results Path:</p>
                <p className="font-semibold font-mono text-xs">{experiment.results_path}</p>
              </div>
            )}
          </div>
        </Tile>
      </div>

      {experiment.status === "queued" && (
        <InlineNotification
          kind="info"
          title="Experiment Queued"
          subtitle="This experiment is waiting to be executed. Background execution is not yet implemented."
          className="mt-6"
        />
      )}
    </div>
  );
}

// Made with Bob
