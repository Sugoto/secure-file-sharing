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
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Share {fileName}</DialogTitle>
        </DialogHeader>

        <Tabs
          value={shareType}
          // @ts-ignore
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
        </Tabs>

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

        {shareLink && (
          <div className="space-y-2">
            <Label htmlFor="shareLink">Share Link</Label>
            <Input
              id="shareLink"
              value={shareLink}
              readOnly
              className="bg-muted"
            />
          </div>
        )}

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleShare}>Share</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
