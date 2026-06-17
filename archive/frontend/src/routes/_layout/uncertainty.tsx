import { createFileRoute } from "@tanstack/react-router";
import { Tabs, TabList, Tab, TabPanels, TabPanel } from "@carbon/react";
import { useState } from "react";

import DataDashboard from "@/components/uncertainty/DataDashboard";
import ExperimentConfig from "@/components/uncertainty/ExperimentConfig";
import ResultsView from "@/components/uncertainty/ResultsView";

export const Route = createFileRoute("/_layout/uncertainty")({
  component: UncertaintyClassification,
});

function UncertaintyClassification() {
  const [selectedTab, setSelectedTab] = useState(0);
  const [selectedExperimentId, setSelectedExperimentId] = useState<string | null>(null);

  return (
    <div className="w-full">
      <h1 className="sm:text-left py-12 text-center text-2xl font-bold">
        Uncertainty Classification Platform
      </h1>

      <Tabs selectedIndex={selectedTab} onChange={(evt) => setSelectedTab(evt.selectedIndex)}>
        <TabList aria-label="Uncertainty workflow tabs" contained>
          <Tab>Data Dashboard</Tab>
          <Tab>Configuration & Training</Tab>
          <Tab disabled={!selectedExperimentId}>Results</Tab>
        </TabList>
        <TabPanels>
          <TabPanel>
            <DataDashboard />
          </TabPanel>
          <TabPanel>
            <ExperimentConfig 
              onExperimentCreated={(id) => {
                setSelectedExperimentId(id);
                setSelectedTab(2);
              }}
            />
          </TabPanel>
          <TabPanel>
            {selectedExperimentId && (
              <ResultsView experimentId={selectedExperimentId} />
            )}
          </TabPanel>
        </TabPanels>
      </Tabs>
    </div>
  );
}

// Made with Bob
