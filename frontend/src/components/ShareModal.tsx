import { useState } from "react";
import { useFileStore } from "../store/fileStore";

interface ShareModalProps {
  fileId: number;
  fileName: string;
  onClose: () => void;
}

export const ShareModal = ({ fileId, fileName, onClose }: ShareModalProps) => {
  const [username, setUsername] = useState("");
  const [expiresIn, setExpiresIn] = useState(24);
  const [shareType, setShareType] = useState<"user" | "link">("user");
  const [shareLink, setShareLink] = useState("");
  const { shareFile } = useFileStore();

  const handleShare = async () => {
    if (shareType === "user" && !username) return;
    
    const { token } = await shareFile(
      fileId,
      shareType === "user" ? username : undefined,
      expiresIn
    );

    if (shareType === "link" && token) {
      setShareLink(`${window.location.origin}/shared/${token}`);
    } else {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg w-96">
        <h3 className="text-lg font-semibold mb-4">Share {fileName}</h3>
        
        <div className="mb-4">
          <label className="block mb-2">Share Type</label>
          <div className="flex gap-4">
            <button
              className={`px-4 py-2 rounded ${
                shareType === "user" ? "bg-blue-600 text-white" : "bg-gray-200"
              }`}
              onClick={() => setShareType("user")}
            >
              Share with User
            </button>
            <button
              className={`px-4 py-2 rounded ${
                shareType === "link" ? "bg-blue-600 text-white" : "bg-gray-200"
              }`}
              onClick={() => setShareType("link")}
            >
              Generate Link
            </button>
          </div>
        </div>

        {shareType === "user" && (
          <div className="mb-4">
            <label className="block mb-2">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border rounded"
              placeholder="Enter username"
            />
          </div>
        )}

        <div className="mb-4">
          <label className="block mb-2">Expires In (hours)</label>
          <input
            type="number"
            value={expiresIn}
            onChange={(e) => setExpiresIn(parseInt(e.target.value))}
            className="w-full px-3 py-2 border rounded"
            min="1"
          />
        </div>

        {shareLink && (
          <div className="mb-4">
            <label className="block mb-2">Share Link</label>
            <input
              type="text"
              value={shareLink}
              readOnly
              className="w-full px-3 py-2 border rounded bg-gray-50"
            />
          </div>
        )}

        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm bg-gray-200 rounded hover:bg-gray-300"
          >
            Cancel
          </button>
          <button
            onClick={handleShare}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Share
          </button>
        </div>
      </div>
    </div>
  );
};
