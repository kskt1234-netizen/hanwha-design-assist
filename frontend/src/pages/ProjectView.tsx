import { useCallback, useEffect, useState } from "react";
import { App as AntApp, Tabs, Typography } from "antd";
import { api } from "../api";
import type { DesignState, Project, StageKey } from "../types";
import StageToolbar from "./StageToolbar";
import DocumentsTab from "./DocumentsTab";
import RequirementsTab from "./RequirementsTab";
import FeaturesTab from "./FeaturesTab";
import DataModelTab from "./DataModelTab";
import TraceTab from "./TraceTab";
import ReviewTab from "./ReviewTab";

const EMPTY: DesignState = { requirements: [], features: [], entities: [], relationships: [] };

export default function ProjectView({ projectId, onChanged }: { projectId: number; onChanged: () => void }) {
  const { message } = AntApp.useApp();
  const [project, setProject] = useState<Project | null>(null);
  const [draft, setDraft] = useState<DesignState>(EMPTY);
  const [dirty, setDirty] = useState<Record<StageKey, boolean>>({ requirements: false, features: false, data_model: false });
  const [busy, setBusy] = useState(false);
  const [tab, setTab] = useState("documents");
  const [revision, setRevision] = useState(0); // 서버 상태가 바뀔 때 하위 탭이 다시 불러오도록

  const reload = useCallback(async () => {
    const [p, d] = await Promise.all([api.project(projectId), api.design(projectId)]);
    setProject(p);
    setDraft(d);
    setDirty({ requirements: false, features: false, data_model: false });
    setRevision((r) => r + 1);
  }, [projectId]);

  useEffect(() => {
    reload().catch((e) => message.error(e.message));
  }, [reload, message]);

  const run = async (fn: () => Promise<unknown>, done: string) => {
    setBusy(true);
    try {
      await fn();
      await reload();
      onChanged();
      message.success(done);
    } catch (e) {
      message.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const update = (stage: StageKey, patch: Partial<DesignState>) => {
    setDraft((d) => ({ ...d, ...patch }));
    setDirty((x) => ({ ...x, [stage]: true }));
  };

  const save = (stage: StageKey) => {
    if (stage === "requirements") return api.saveRequirements(projectId, draft.requirements);
    if (stage === "features") return api.saveFeatures(projectId, draft.features);
    return api.saveDataModel(projectId, draft.entities, draft.relationships);
  };

  const canGenerate: Record<StageKey, boolean> = {
    requirements: (project?.document_count ?? 0) > 0,
    features: draft.requirements.length > 0,
    data_model: draft.features.length > 0,
  };

  const toolbar = (stage: StageKey) => (
    <StageToolbar
      status={project?.stage_status[stage] ?? "EMPTY"}
      dirty={dirty[stage]}
      busy={busy}
      canGenerate={canGenerate[stage] && !dirty[stage]}
      onGenerate={() => run(() => api.generate(projectId, stage), "AI 초안을 생성했습니다.")}
      onSave={() => run(() => save(stage), "저장했습니다.")}
      onApprove={() => run(() => api.approve(projectId, stage), "승인했습니다. 버전이 기록되었습니다.")}
    />
  );

  if (!project) return null;

  return (
    <>
      <Typography.Title level={4} style={{ marginTop: 0 }}>{project.name}</Typography.Title>
      <Tabs
        activeKey={tab}
        onChange={setTab}
        items={[
          { key: "documents", label: "1. 요구사항 문서", children: <DocumentsTab projectId={projectId} onChanged={reload} /> },
          {
            key: "requirements", label: "2. 요구사항 분석",
            children: <>{toolbar("requirements")}<RequirementsTab value={draft.requirements} onChange={(requirements) => update("requirements", { requirements })} /></>,
          },
          {
            key: "features", label: "3. 기능 명세서",
            children: <>{toolbar("features")}<FeaturesTab value={draft.features} requirements={draft.requirements} onChange={(features) => update("features", { features })} /></>,
          },
          {
            key: "data_model", label: "4. 데이터 모델 (ERD·DDL)",
            children: (
              <>
                {toolbar("data_model")}
                <DataModelTab
                  projectId={projectId}
                  revision={revision}
                  state={draft}
                  dirty={dirty.data_model}
                  onChange={(patch) => update("data_model", patch)}
                />
              </>
            ),
          },
          { key: "trace", label: "5. 추적표", children: <TraceTab projectId={projectId} revision={revision} /> },
          { key: "review", label: "6. 설계 검토", children: <ReviewTab projectId={projectId} revision={revision} /> },
        ]}
      />
    </>
  );
}
