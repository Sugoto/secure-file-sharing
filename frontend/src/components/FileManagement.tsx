import { useEffect, useState } from "react";
import { useFileStore } from "../store/fileStore";
import { fileService } from "../services/fileService";
import { ShareModal } from "./ShareModal";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Download, Share2, Trash2, Plus } from "lucide-react";
import { FileUploadModal } from "./FileUploadModal";

export const FileManagement = () => {
  const { ownedFiles, sharedFiles, fetchFiles, deleteFile, isLoading, error } =
    useFileStore();
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);
  const [shareFileId, setShareFileId] = useState<number | null>(null);
  const [shareFileName, setShareFileName] = useState("");
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const currentUser = JSON.parse(localStorage.getItem("user") || "{}");
  const isGuest = currentUser.role === "guest";

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  const FileRow = ({
    file,
    isOwned,
    permission,
  }: {
    file: {
      id: number;
      filename: string;
      file_path: string;
      user_id: number;
    };
    isOwned: boolean;
    permission?: "view" | "download";
  }) => {
    const [downloadPassword, setDownloadPassword] = useState("");
    const [downloadError, setDownloadError] = useState("");

    const handleDownload = async () => {
      try {
        setDownloadError("");
        const blob = await fileService.downloadFile(
          file.id,
          downloadPassword,
          file.filename
        );
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = file.filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        setDownloadPassword("");
        setSelectedFileId(null);
      } catch (error: any) {
        const errorMessage =
          error.response?.data?.detail || "An error occurred during download";
        setDownloadError(errorMessage);
        console.error("Download failed:", error);
      }
    };

    return (
      <div className="flex items-center justify-between p-4 border-b last:border-b-0">
        <div className="flex items-center gap-4">
          <span className="text-sm">{file.filename}</span>
        </div>
        <div className="flex gap-2">
          {selectedFileId === file.id ? (
            <div className="flex flex-col gap-2">
              <div className="flex gap-2">
                <Input
                  type="password"
                  value={downloadPassword}
                  onChange={(e) => setDownloadPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-40"
                />
                <Button size="sm" variant="default" onClick={handleDownload}>
                  Confirm
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setSelectedFileId(null);
                    setDownloadPassword("");
                    setDownloadError("");
                  }}
                >
                  Cancel
                </Button>
              </div>
              {downloadError && (
                <p className="text-sm text-red-500">{downloadError}</p>
              )}
            </div>
          ) : (
            <>
              {(!permission || permission === "download") && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setSelectedFileId(file.id)}
                >
                  <Download className="h-4 w-4" />
                </Button>
              )}
              {isOwned && (
                <>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setShareFileId(file.id);
                      setShareFileName(file.filename);
                    }}
                  >
                    <Share2 className="h-4 w-4" />
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
            </>
          )}
        </div>
      </div>
    );
  };

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Files</h2>
        {!isGuest && (
          <Button onClick={() => setIsUploadModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> Upload File
          </Button>
        )}
      </div>

      {!isGuest && (
        <Card>
          <CardHeader>
            <CardTitle>Your Files</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-h-[300px] overflow-y-auto">
              {ownedFiles.map((file) => (
                <FileRow key={file.id} file={file} isOwned={true} />
              ))}
              {ownedFiles.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No files uploaded yet
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Shared With You</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="max-h-[300px] overflow-y-auto">
            {sharedFiles.map((file) => (
              <FileRow
                key={file.id}
                file={file}
                isOwned={false}
                permission={file.permission}
              />
            ))}
            {sharedFiles.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No files shared with you
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {shareFileId && (
        <ShareModal
          fileId={shareFileId}
          fileName={shareFileName}
          onClose={() => setShareFileId(null)}
        />
      )}

      {!isGuest && (
        <FileUploadModal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
        />
      )}
    </div>
  );
};
