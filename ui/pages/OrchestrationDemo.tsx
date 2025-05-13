"use client";
import React, { useState } from "react";

interface Step {
  agent: string;
  prompt: string;
  model: string;
  condition?: string;
  parallel_group?: string;
}

interface WorkflowResult {
  steps: any[];
  input_data?: any;
}

export default function OrchestrationDemo() {
  // ...estado anterior...
  const [executions, setExecutions] = useState<any[]>([]);
  const [loadingExecutions, setLoadingExecutions] = useState(false);
  const [selectedExec, setSelectedExec] = useState<any | null>(null);

  // Cargar historial de ejecuciones
  const fetchExecutions = async () => {
    setLoadingExecutions(true);
    try {
      const resp = await fetch("/api/v1/executions", {
        headers: { "Authorization": `Bearer ${jwt}` }
      });
      if (!resp.ok) throw new Error(await resp.text());
      const data = await resp.json();
      setExecutions(data.data || []);
    } catch (err: any) {
      setError("Error al obtener historial de ejecuciones");
    }
    setLoadingExecutions(false);
  };
  const handleViewExecution = async (id: string) => {
    setLoadingExecutions(true);
    try {
      const resp = await fetch(`/api/v1/executions/${id}`, {
        headers: { "Authorization": `Bearer ${jwt}` }
      });
      if (!resp.ok) throw new Error(await resp.text());
      const data = await resp.json();
      setSelectedExec(data.data);
    } catch (err: any) {
      setError("No se pudo consultar la ejecución");
    }
    setLoadingExecutions(false);
  };

  const [steps, setSteps] = useState<Step[]>([
    { agent: "a1", prompt: "¿Eres mayor de edad?", model: "claude-v1" },
  ]);
  const [workflow, setWorkflow] = useState("demo_ui");
  const [jwt, setJwt] = useState("testtoken");
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [loadingWorkflows, setLoadingWorkflows] = useState(false);

  // Cargar workflows guardados al montar
  React.useEffect(() => {
    fetchWorkflows();
  }, []);
  const fetchWorkflows = async () => {
    setLoadingWorkflows(true);
    try {
      const resp = await fetch("/api/v1/workflows", {
        headers: { "Authorization": `Bearer ${jwt}` }
      });
      if (!resp.ok) throw new Error(await resp.text());
      const data = await resp.json();
      setWorkflows(data.data || []);
    } catch (err: any) {
      setError("Error al obtener workflows guardados");
    }
    setLoadingWorkflows(false);
  };
  const handleLoadWorkflow = async (name: string) => {
    setLoading(true);
    setError("");
    try {
      const resp = await fetch(`/api/v1/workflows/${name}`, {
        headers: { "Authorization": `Bearer ${jwt}` }
      });
      if (!resp.ok) throw new Error(await resp.text());
      const data = await resp.json();
      setWorkflow(data.data.workflow);
      setSteps(data.data.steps);
    } catch (err: any) {
      setError("No se pudo cargar el workflow");
    }
    setLoading(false);
  };
  const handleDeleteWorkflow = async (name: string) => {
    if (!window.confirm(`¿Eliminar workflow '${name}'?`)) return;
    setLoading(true);
    setError("");
    try {
      const resp = await fetch(`/api/v1/workflows/${name}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${jwt}` }
      });
      if (!resp.ok) throw new Error(await resp.text());
      await fetchWorkflows();
    } catch (err: any) {
      setError("No se pudo eliminar el workflow");
    }
    setLoading(false);
  };
  const handleSaveWorkflow = async () => {
    setLoading(true);
    setError("");
    try {
      const resp = await fetch("/api/v1/workflows", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${jwt}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ workflow, steps }),
      });
      if (!resp.ok) throw new Error(await resp.text());
      await fetchWorkflows();
    } catch (err: any) {
      setError("No se pudo guardar el workflow");
    }
    setLoading(false);
  };

  const handleStepChange = (i: number, field: keyof Step, value: string) => {
    const newSteps = [...steps];
    newSteps[i][field] = value;
    setSteps(newSteps);
  };

  const addStep = () => {
    setSteps([
      ...steps,
      { agent: "", prompt: "", model: "claude-v1" },
    ]);
  };

  const removeStep = (i: number) => {
    setSteps(steps.filter((_, idx) => idx !== i));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const resp = await fetch("/api/v1/workflows/execute", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${jwt}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ workflow, steps }),
      });
      if (!resp.ok) throw new Error(await resp.text());
      const data = await resp.json();
      setResult(data.data);
    } catch (err: any) {
      setError(err.message || "Error desconocido");
    }
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 24 }}>
      <h1>Demo Orquestación Multi-Agente</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Nombre del workflow:
          <input
            value={workflow}
            onChange={e => setWorkflow(e.target.value)}
            style={{ marginLeft: 8 }}
            required
          />
        </label>
        <br />
        <label>
          JWT:
          <input
            value={jwt}
            onChange={e => setJwt(e.target.value)}
            style={{ marginLeft: 8, width: 300 }}
            required
          />
        </label>
        <br /><br />
        <b>Pasos del workflow:</b>
        {steps.map((step, i) => (
          <div key={i} style={{ border: "1px solid #ccc", padding: 12, margin: 8, borderRadius: 8 }}>
            <label>
              Agente:
              <input
                value={step.agent}
                onChange={e => handleStepChange(i, "agent", e.target.value)}
                required
                style={{ marginLeft: 8, width: 100 }}
              />
            </label>
            <label style={{ marginLeft: 16 }}>
              Prompt:
              <input
                value={step.prompt}
                onChange={e => handleStepChange(i, "prompt", e.target.value)}
                required
                style={{ marginLeft: 8, width: 200 }}
              />
            </label>
            <label style={{ marginLeft: 16 }}>
              Modelo:
              <input
                value={step.model}
                onChange={e => handleStepChange(i, "model", e.target.value)}
                required
                style={{ marginLeft: 8, width: 120 }}
              />
            </label>
            <label style={{ marginLeft: 16 }}>
              Condition:
              <input
                value={step.condition || ""}
                onChange={e => handleStepChange(i, "condition", e.target.value)}
                placeholder="Opcional"
                style={{ marginLeft: 8, width: 200 }}
              />
            </label>
            <label style={{ marginLeft: 16 }}>
              Parallel Group:
              <input
                value={step.parallel_group || ""}
                onChange={e => handleStepChange(i, "parallel_group", e.target.value)}
                placeholder="Opcional"
                style={{ marginLeft: 8, width: 120 }}
              />
            </label>
            <button type="button" onClick={() => removeStep(i)} style={{ marginLeft: 16, color: "red" }}>
              Eliminar
            </button>
          </div>
        ))}
        <button type="button" onClick={addStep} style={{ marginTop: 8 }}>
          + Agregar paso
        </button>
        <br /><br />
        <button type="submit" disabled={loading}>
          Ejecutar workflow
        </button>
      </form>
      {loading && <p>Ejecutando workflow...</p>}
      {error && <p style={{ color: "red" }}>Error: {error}</p>}
      {result && (
        <div style={{ marginTop: 32 }}>
          <h2>Resultado</h2>
          <pre style={{ background: "#f6f6f6", padding: 16, borderRadius: 8 }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}

      <div style={{ marginTop: 48 }}>
        <h2>Historial de Ejecuciones</h2>
        <button onClick={fetchExecutions} disabled={loadingExecutions}>
          Refrescar historial
        </button>
        {loadingExecutions && <span style={{ marginLeft: 12 }}>Cargando...</span>}
        <table style={{ width: "100%", marginTop: 16, borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#eee" }}>
              <th style={{ padding: 6, border: "1px solid #ccc" }}>ID</th>
              <th style={{ padding: 6, border: "1px solid #ccc" }}>Workflow</th>
              <th style={{ padding: 6, border: "1px solid #ccc" }}>Inicio</th>
              <th style={{ padding: 6, border: "1px solid #ccc" }}>Fin</th>
              <th style={{ padding: 6, border: "1px solid #ccc" }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {executions.map((ex) => (
              <tr key={ex.id}>
                <td style={{ padding: 6, border: "1px solid #ccc", fontSize: 12 }}>{ex.id}</td>
                <td style={{ padding: 6, border: "1px solid #ccc" }}>{ex.workflow}</td>
                <td style={{ padding: 6, border: "1px solid #ccc" }}>{ex.started_at?.replace("T", " ").slice(0, 19)}</td>
                <td style={{ padding: 6, border: "1px solid #ccc" }}>{ex.finished_at?.replace("T", " ").slice(0, 19)}</td>
                <td style={{ padding: 6, border: "1px solid #ccc" }}>
                  <button onClick={() => handleViewExecution(ex.id)}>
                    Ver detalle
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {selectedExec && (
          <div style={{ marginTop: 24, background: "#f6f6f6", padding: 16, borderRadius: 8 }}>
            <h3>Detalle de Ejecución</h3>
            <button onClick={() => setSelectedExec(null)} style={{ float: "right" }}>Cerrar</button>
            <pre style={{ fontSize: 13 }}>
              {JSON.stringify(selectedExec, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
