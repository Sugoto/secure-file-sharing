import { useEffect, useState } from "react";
import { useFileStore } from "../../store/fileStore";
import { fileService } from "../../services/fileService";
import { ShareModal } from "../ShareModal/ShareModal";

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
    <div className="flex items-center justify-between p-4 border-b">
      <span>{file.filename}</span>
      <div className="flex gap-2">
        {selectedFileId === file.id ? (
          <div className="flex gap-2">
            <input
              type="password"
              value={downloadPassword}
              onChange={(e) => setDownloadPassword(e.target.value)}
              placeholder="Enter password"
              className="px-2 py-1 border rounded"
            />
            <button
              onClick={() => handleDownload(file.id)}
              className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
            >
              Confirm
            </button>
            <button
              onClick={() => setSelectedFileId(null)}
              className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Cancel
            </button>
          </div>
        ) : (
          <>
            <button
              onClick={() => setSelectedFileId(file.id)}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Download
            </button>
            <button
              onClick={() => {
                setShareFileId(file.id);
                setShareFileName(file.filename);
              }}
              className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
            >
              Share
            </button>
            <button
              onClick={() => deleteFile(file.id)}
              className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
            >
              Delete
            </button>
          </>
        )}
      </div>
    </div>
  );

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-4">Your Files</h2>
        <div className="border rounded-lg overflow-hidden">
          {ownedFiles.map((file) => (
            <FileRow key={file.id} file={file} />
          ))}
          {ownedFiles.length === 0 && (
            <p className="p-4 text-gray-500">No files uploaded yet</p>
          )}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4">Shared With You</h2>
        <div className="border rounded-lg overflow-hidden">
          {sharedFiles.map((file) => (
            <FileRow key={file.id} file={file} />
          ))}
          {sharedFiles.length === 0 && (
            <p className="p-4 text-gray-500">No files shared with you</p>
          )}
        </div>
      </div>

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
