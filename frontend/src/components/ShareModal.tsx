import { useState } from "react";
import { useFileStore } from "../store/fileStore";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "./ui/dialog";
import { TabsTrigger, TabsList, TabsContent, Tabs } from "./ui/tabs";
import { ToggleGroup, ToggleGroupItem } from "./ui/toggle-group";
import { EyeIcon, DownloadIcon } from "lucide-react";

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
  const [permission, setPermission] = useState<"view" | "download">("view");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const { shareFile } = useFileStore();

  const handleShare = async () => {
    if (shareType === "user" && !username) {
      setError("Please enter a username");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const shareData = {
        file_id: fileId,
        shared_with_username: shareType === "user" ? username : undefined,
        permissions: permission,
        expires_in_hours: expiresIn,
      };

      const response = await shareFile(shareData);

      if (shareType === "link" && response?.share_token) {
        setShareLink(
          `${window.location.origin}/shared/${response.share_token}`
        );
      } else if (shareType === "user") {
        onClose();
      }
    } catch (err) {
      setError("Failed to share file. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Share {fileName}</DialogTitle>
        </DialogHeader>

        <Tabs
          value={shareType}
          onValueChange={(value: "user" | "link") => setShareType(value)}
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="user">Share with User</TabsTrigger>
            <TabsTrigger value="link">Generate Link</TabsTrigger>
          </TabsList>

          <TabsContent value="user" className="mt-4">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter username"
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="link" className="mt-4">
            <div className="space-y-4">
              {shareLink ? (
                <div className="space-y-2">
                  <Label htmlFor="shareLink">Share Link</Label>
                  <div className="flex gap-2">
                    <Input
                      id="shareLink"
                      value={shareLink}
                      readOnly
                      className="bg-muted"
                    />
                    <Button
                      variant="outline"
                      onClick={() => navigator.clipboard.writeText(shareLink)}
                    >
                      Copy
                    </Button>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Click Share to generate a link
                </p>
              )}
            </div>
          </TabsContent>
        </Tabs>

        <div className="space-y-2">
          <Label>Permission</Label>
          <ToggleGroup
            type="single"
            value={permission}
            onValueChange={(value) =>
              setPermission(value as "view" | "download")
            }
            className="justify-start"
          >
            <ToggleGroupItem value="view" aria-label="View only">
              <EyeIcon className="h-4 w-4 mr-2" />
              View
            </ToggleGroupItem>
            <ToggleGroupItem value="download" aria-label="Download">
              <DownloadIcon className="h-4 w-4 mr-2" />
              Download
            </ToggleGroupItem>
          </ToggleGroup>
        </div>

        <div className="space-y-2">
          <Label htmlFor="expires">Expires In (hours)</Label>
          <Input
            id="expires"
            type="number"
            value={expiresIn}
            onChange={(e) => setExpiresIn(parseInt(e.target.value))}
            min="1"
          />
        </div>

        {error && <p className="text-sm text-red-500">{error}</p>}

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleShare} disabled={isLoading}>
            {isLoading ? "Sharing..." : "Share"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
