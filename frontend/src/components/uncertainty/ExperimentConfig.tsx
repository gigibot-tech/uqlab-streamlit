import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Form,
  TextInput,
  NumberInput,
  Select,
  SelectItem,
  Button,
  Loading,
  InlineNotification,
} from "@carbon/react";
import { Add } from "@carbon/icons-react";

interface ExperimentConfigProps {
  onExperimentCreated?: (id: string) => void;
}

export default function ExperimentConfig({ onExperimentCreated }: ExperimentConfigProps) {
  const [formData, setFormData] = useState({
    name: "",
    noise_type: "worse_label",
    under_supported_classes: "3,5",
    under_train_per_class: 50,
    regular_train_per_class: 300,
    eval_per_group: 600,
    dinov2_model: "small",
    hidden_dim: 256,
    dropout: 0.2,
    epochs: 12,
    learning_rate: 0.001,
    weight_decay: 0.0001,
    train_batch_size: 256,
    mc_passes: 20,
  });

  const createMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const response = await fetch("/api/v1/experiments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: data.name,
          config: {
            noise_type: data.noise_type,
            under_supported_classes: data.under_supported_classes,
            under_train_per_class: data.under_train_per_class,
            regular_train_per_class: data.regular_train_per_class,
            eval_per_group: data.eval_per_group,
            dinov2_model: data.dinov2_model,
            hidden_dim: data.hidden_dim,
            dropout: data.dropout,
            epochs: data.epochs,
            learning_rate: data.learning_rate,
            weight_decay: data.weight_decay,
            train_batch_size: data.train_batch_size,
            mc_passes: data.mc_passes,
            attribution_method: "dualxda",
          },
        }),
      });
      if (!response.ok) throw new Error("Failed to create experiment");
      return response.json();
    },
    onSuccess: (data) => {
      if (onExperimentCreated) {
        onExperimentCreated(data.id);
      }
    },
  });

  const { data: experiments, isLoading } = useQuery({
    queryKey: ["experiments"],
    queryFn: async () => {
      const response = await fetch("/api/v1/experiments");
      if (!response.ok) throw new Error("Failed to fetch experiments");
      return response.json();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  if (isLoading) {
    return <Loading description="Loading experiments..." />;
  }

  return (
    <div className="py-6">
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Create New Experiment</h2>
        
        {createMutation.isError && (
          <InlineNotification
            kind="error"
            title="Error"
            subtitle="Failed to create experiment"
            className="mb-4"
          />
        )}
        
        {createMutation.isSuccess && (
          <InlineNotification
            kind="success"
            title="Success"
            subtitle="Experiment created successfully"
            className="mb-4"
          />
        )}

        <Form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TextInput
              id="name"
              labelText="Experiment Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />

            <Select
              id="dinov2_model"
              labelText="DINOv2 Model Size"
              value={formData.dinov2_model}
              onChange={(e) => setFormData({ ...formData, dinov2_model: e.target.value })}
            >
              <SelectItem value="small" text="Small (Fast)" />
              <SelectItem value="base" text="Base (Balanced)" />
              <SelectItem value="large" text="Large (Accurate)" />
            </Select>

            <NumberInput
              id="epochs"
              label="Training Epochs"
              value={formData.epochs}
              onChange={(e, { value }) => setFormData({ ...formData, epochs: value || 12 })}
              min={1}
              max={100}
            />

            <NumberInput
              id="under_train_per_class"
              label="Under-supported Samples/Class"
              value={formData.under_train_per_class}
              onChange={(e, { value }) => setFormData({ ...formData, under_train_per_class: value || 50 })}
              min={10}
              max={500}
            />

            <NumberInput
              id="regular_train_per_class"
              label="Regular Samples/Class"
              value={formData.regular_train_per_class}
              onChange={(e, { value }) => setFormData({ ...formData, regular_train_per_class: value || 300 })}
              min={50}
              max={1000}
            />

            <NumberInput
              id="mc_passes"
              label="MC Dropout Passes"
              value={formData.mc_passes}
              onChange={(e, { value }) => setFormData({ ...formData, mc_passes: value || 20 })}
              min={5}
              max={100}
            />
          </div>

          <Button
            type="submit"
            renderIcon={Add}
            className="mt-6"
            disabled={createMutation.isPending || !formData.name}
          >
            {createMutation.isPending ? "Creating..." : "Create Experiment"}
          </Button>
        </Form>
      </div>

      <div className="mt-12">
        <h2 className="text-xl font-semibold mb-4">Recent Experiments</h2>
        {experiments && experiments.length > 0 ? (
          <div className="space-y-2">
            {experiments.slice(0, 5).map((exp: any) => (
              <div key={exp.id} className="p-4 border rounded">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-semibold">{exp.name}</h3>
                    <p className="text-sm text-gray-600">
                      Status: {exp.status} | Created: {new Date(exp.created_at).toLocaleString()}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => onExperimentCreated && onExperimentCreated(exp.id)}
                  >
                    View Results
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">No experiments yet. Create one to get started!</p>
        )}
      </div>
    </div>
  );
}

// Made with Bob
