import { useState } from "react";
import { useParams } from "react-router-dom";
import { Lock, Download } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
  CardDescription,
  CardTitle,
} from "./ui/card";
import { fileService } from "../services/fileService";

export const SharedFilePage = () => {
  const { token } = useParams();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleDownload = async () => {
    if (!password) {
      setError("Please enter the file password");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const decryptedFile = await fileService.accessSharedFile(
        token!,
        password
      );
      const url = window.URL.createObjectURL(decryptedFile);
      const a = document.createElement("a");
      a.href = url;
      a.download = decryptedFile.name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error: any) {
      setError(error.response?.data?.detail || "Failed to access file");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-center mb-2">
            <Lock className="h-8 w-8 text-muted-foreground" />
          </div>
          <CardTitle className="text-2xl font-bold text-center">
            Access Shared File
          </CardTitle>
          <CardDescription className="text-center">
            Enter the password to access the shared file
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter file password"
              className="w-full"
            />
          </div>
          {error && <p className="text-sm text-red-500 text-center">{error}</p>}
        </CardContent>
        <CardFooter>
          <Button
            onClick={handleDownload}
            disabled={isLoading}
            className="w-full"
            variant="default"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                Accessing...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Download className="h-4 w-4" />
                Submit
              </span>
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};
