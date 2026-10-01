import { useEffect, useState } from "react";
import { App as AntApp, Button, Select, Space, Table, Tag, Typography } from "antd";
import { api } from "../api";
import type { Issue } from "../types";

const SEVERITY = { ERROR: "red", WARN: "orange", INFO: "blue" } as const;
const RULES: Record<string, string> = {
  R01: "요구사항 누락", R02: "근거 없는 기능", R03: "테이블 없는 기능", R04: "기능 없는 테이블",
  R05: "테이블 형식", R06: "FK 오류", R07: "N:M 관계", R08: "명명 규칙", R09: "DDL 실행",
  L01: "요구사항 상충", L02: "모델 누락 데이터", L03: "비기능 미반영",
};

export default function ReviewTab({ projectId, revision }: { projectId: number; revision: number }) {
  const { message } = AntApp.useApp();
  const [issues, setIssues] = useState<Issue[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.issues(projectId).then(setIssues);
  }, [projectId, revision]);

  const runReview = async () => {
    setBusy(true);
    try {
      const list = await api.review(projectId);
      setIssues(list);
      message.success(`검토 완료: ${list.length}건`);
    } catch (e) {
      message.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" loading={busy} onClick={runReview}>검토 실행</Button>
        <Typography.Text type="secondary">저장된 설계 기준으로 규칙 검사(R01~R09)와 AI 검토(L01~L03)를 합니다.</Typography.Text>
      </Space>
      <Table
        rowKey="id"
        dataSource={issues}
        size="small"
        pagination={false}
        locale={{ emptyText: "발견된 문제가 없습니다" }}
        columns={[
          { title: "심각도", width: 80, render: (_, i) => <Tag color={SEVERITY[i.severity]}>{i.severity}</Tag> },
          { title: "규칙", width: 150, render: (_, i) => `${i.rule_code} ${RULES[i.rule_code] ?? ""}` },
          { title: "대상", width: 160, render: (_, i) => i.target_code },
          { title: "내용", dataIndex: "message" },
          {
            title: "상태", width: 120,
            render: (_, i) => (
              <Select
                value={i.status}
                style={{ width: "100%" }}
                options={[{ value: "OPEN", label: "미해결" }, { value: "RESOLVED", label: "해결" }, { value: "IGNORED", label: "무시" }]}
                onChange={async (status) => {
                  const updated = await api.setIssueStatus(projectId, i.id, status);
                  setIssues((xs) => xs.map((x) => (x.id === i.id ? updated : x)));
                }}
              />
            ),
          },
        ]}
      />
    </>
  );
}
