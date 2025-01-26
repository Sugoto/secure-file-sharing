import { useEffect, useState } from "react";
import { useFileStore } from "../store/fileStore";
import { fileService } from "../services/fileService";
import { ShareModal } from "./ShareModal";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Download, Share, Trash2 } from "lucide-react";

export const FileList = () => {
  const { ownedFiles, sharedFiles, fetchFiles, deleteFile, isLoading, error } =
    useFileStore();
  const [downloadPassword, setDownloadPassword] = useState("");
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);
  const [shareFileId, setShareFileId] = useState<number | null>(null);
  const [shareFileName, setShareFileName] = useState("");

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  const handleDownload = async (fileId: number) => {
    try {
      const blob = await fileService.downloadFile(fileId, downloadPassword);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download =
        ownedFiles.find((f) => f.id === fileId)?.filename || "download";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      setDownloadPassword("");
      setSelectedFileId(null);
    } catch (err) {
      console.error("Download failed:", err);
    }
  };

  const FileRow = ({ file }: { file: { id: number; filename: string } }) => (
    <div className="flex items-center justify-between p-4 border-b last:border-b-0">
      <span className="text-sm">{file.filename}</span>
      <div className="flex gap-2">
        {selectedFileId === file.id ? (
          <div className="flex gap-2">
            <Input
              type="password"
              value={downloadPassword}
              onChange={(e) => setDownloadPassword(e.target.value)}
              placeholder="Enter password"
              className="w-40"
            />
            <Button
              size="sm"
              variant="default"
              onClick={() => handleDownload(file.id)}
            >
              Confirm
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setSelectedFileId(null)}
            >
              Cancel
            </Button>
          </div>
        ) : (
          <>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setSelectedFileId(file.id)}
            >
              <Download className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setShareFileId(file.id);
                setShareFileName(file.filename);
              }}
            >
              <Share className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => deleteFile(file.id)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </>
        )}
      </div>
    </div>
  );

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Your Files</CardTitle>
        </CardHeader>
        <CardContent>
          {ownedFiles.map((file) => (
            <FileRow key={file.id} file={file} />
          ))}
          {ownedFiles.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No files uploaded yet
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Shared With You</CardTitle>
        </CardHeader>
        <CardContent>
          {sharedFiles.map((file) => (
            <FileRow key={file.id} file={file} />
          ))}
          {sharedFiles.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No files shared with you
            </p>
          )}
        </CardContent>
      </Card>

      {shareFileId && (
        <ShareModal
          fileId={shareFileId}
          fileName={shareFileName}
          onClose={() => setShareFileId(null)}
        />
      )}
    </div>
  );
};
