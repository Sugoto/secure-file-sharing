export const sanitizeFileName = (fileName: string): string => {
  return fileName
    .replace(/[^\w\-. ]/g, "")
    .replace(/\.{2,}/g, ".")
    .trim();
};

export const sanitizeInput = (input: string): string => {
  if (!input) return "";
  return input
    .replace(/[<>'"&;]/g, "")
    .replace(/[^\w\s\-_.@]/g, "")
    .trim();
};

export const sanitizePassword = (password: string): string => {
  return password.replace(/[^\w!@#$%^&*\-=+]/g, "");
};
