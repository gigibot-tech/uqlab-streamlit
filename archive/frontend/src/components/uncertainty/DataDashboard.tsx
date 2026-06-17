import { useQuery } from "@tanstack/react-query";
import {
  DataTable,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  Loading,
  Tile
} from "@carbon/react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "";

export default function DataDashboard() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ["dataset-stats"],
    queryFn: async () => {
      const url = `${API_BASE_URL}/api/v1/datasets/cifar10n/stats?noise_type=worse_label`;
      console.log("Fetching dataset stats from:", url);
      
      const token = localStorage.getItem("access_token");
      const response = await fetch(url, {
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Failed to fetch stats:", response.status, errorText);
        throw new Error(`Failed to fetch stats: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("Received dataset stats:", data);
      return data;
    },
  });

  if (isLoading) {
    return <Loading description="Loading dataset statistics..." />;
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded">
        <h3 className="text-lg font-semibold text-red-800 mb-2">Error loading data</h3>
        <p className="text-red-600">{error instanceof Error ? error.message : "Unknown error"}</p>
        <p className="text-sm text-red-500 mt-2">Check browser console for details</p>
      </div>
    );
  }

  if (!stats) {
    return <div>No data available</div>;
  }

  // Prepare table data
  const classRows = Object.entries(stats.noise_per_class || {}).map(([classId, data]: [string, any]) => ({
    id: classId,
    className: stats.class_names[parseInt(classId)],
    total: data.total,
    noisy: data.noisy,
    clean: data.total - data.noisy,
    noiseRate: `${(data.rate * 100).toFixed(1)}%`,
  }));

  const headers = [
    { key: "className", header: "Class" },
    { key: "total", header: "Total Samples" },
    { key: "clean", header: "Clean" },
    { key: "noisy", header: "Noisy" },
    { key: "noiseRate", header: "Noise Rate" },
  ];

  return (
    <div className="py-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Tile>
          <h3 className="text-lg font-semibold mb-2">Total Samples</h3>
          <p className="text-3xl font-bold">{stats.total_samples?.toLocaleString()}</p>
        </Tile>
        <Tile>
          <h3 className="text-lg font-semibold mb-2">Clean Samples</h3>
          <p className="text-3xl font-bold text-green-600">{stats.clean_samples?.toLocaleString()}</p>
        </Tile>
        <Tile>
          <h3 className="text-lg font-semibold mb-2">Noisy Samples</h3>
          <p className="text-3xl font-bold text-red-600">{stats.noisy_samples?.toLocaleString()}</p>
        </Tile>
        <Tile>
          <h3 className="text-lg font-semibold mb-2">Overall Noise Rate</h3>
          <p className="text-3xl font-bold text-orange-600">{((stats.noise_rate || 0) * 100).toFixed(1)}%</p>
        </Tile>
      </div>

      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Noise Distribution by Class</h2>
        <DataTable rows={classRows} headers={headers}>
          {({ rows, headers, getTableProps, getHeaderProps, getRowProps }) => (
            <TableContainer>
              <Table {...getTableProps()}>
                <TableHead>
                  <TableRow>
                    {headers.map((header) => (
                      <TableHeader {...getHeaderProps({ header })} key={header.key}>
                        {header.header}
                      </TableHeader>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((row) => (
                    <TableRow {...getRowProps({ row })} key={row.id}>
                      {row.cells.map((cell) => (
                        <TableCell key={cell.id}>{cell.value}</TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DataTable>
      </div>
    </div>
  );
}

// Made with Bob
