import { useEffect, useState } from "react";
import { Table, Tag, Typography } from "antd";
import { api } from "../api";
import type { TraceRow } from "../types";

const missing = <Tag color="red">연결 없음</Tag>;

export default function TraceTab({ projectId, revision }: { projectId: number; revision: number }) {
  const [rows, setRows] = useState<TraceRow[]>([]);
  useEffect(() => {
    api.trace(projectId).then(setRows);
  }, [projectId, revision]);

  return (
    <>
      <Typography.Paragraph type="secondary">
        요구사항 → 기능 → 테이블 연결입니다. 빨간 칸은 연결이 빠진 곳입니다. (비기능 요구사항은 기능이 없어도 정상일 수 있습니다)
      </Typography.Paragraph>
      <Table
        rowKey={(r) => `${r.requirement_code}-${r.feature_code}`}
        dataSource={rows}
        size="small"
        pagination={false}
        columns={[
          { title: "요구사항", width: 100, dataIndex: "requirement_code" },
          { title: "내용", dataIndex: "requirement_text" },
          { title: "분류", width: 80, render: (_, r) => (r.requirement_type === "FUNCTIONAL" ? "기능" : "비기능") },
          { title: "기능", width: 220, render: (_, r) => (r.feature_code ? `${r.feature_code} ${r.feature_name}` : missing) },
          {
            title: "테이블", width: 260,
            render: (_, r) => (r.feature_code && r.tables.length === 0 ? missing : r.tables.map((t) => <Tag key={t}>{t}</Tag>)),
          },
        ]}
      />
    </>
  );
}
