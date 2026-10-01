import { useCallback, useEffect, useState } from "react";
import { App as AntApp, Button, Input, List, Space, Upload } from "antd";
import { api } from "../api";
import type { DocumentInfo } from "../types";

export default function DocumentsTab({ projectId, onChanged }: { projectId: number; onChanged: () => void }) {
  const { message } = AntApp.useApp();
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [text, setText] = useState("");

  const load = useCallback(() => api.documents(projectId).then(setDocs), [projectId]);
  useEffect(() => {
    load().catch((e) => message.error(e.message));
  }, [load, message]);

  const after = async () => {
    await load();
    onChanged();
  };

  return (
    <Space direction="vertical" style={{ width: "100%" }} size="large">
      <Upload
        accept=".txt,.md,.pdf,.docx"
        showUploadList={false}
        customRequest={async ({ file, onSuccess, onError }) => {
          try {
            await api.uploadDocument(projectId, file as File);
            onSuccess?.(null);
            message.success("업로드했습니다.");
            await after();
          } catch (e) {
            onError?.(e as Error);
            message.error((e as Error).message);
          }
        }}
      >
        <Button>파일 업로드 (txt, md, pdf, docx)</Button>
      </Upload>
      <div>
        <Input.TextArea rows={8} value={text} onChange={(e) => setText(e.target.value)} placeholder="또는 요구사항 문서를 붙여넣기" />
        <Button
          style={{ marginTop: 8 }}
          disabled={!text.trim()}
          onClick={async () => {
            await api.addTextDocument(projectId, "붙여넣은 문서.txt", text);
            setText("");
            await after();
          }}
        >
          텍스트로 추가
        </Button>
      </div>
      <List
        bordered
        header="입력된 문서"
        dataSource={docs}
        locale={{ emptyText: "아직 문서가 없습니다" }}
        renderItem={(d) => (
          <List.Item
            actions={[
              <Button key="del" size="small" danger onClick={async () => { await api.deleteDocument(projectId, d.id); await after(); }}>
                삭제
              </Button>,
            ]}
          >
            {d.filename} · {d.length.toLocaleString()}자
          </List.Item>
        )}
      />
    </Space>
  );
}
