"""
Common utility functions.
"""

export const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};

export const truncateText = (text: string, length: number): string => {
  return text.length > length ? `${text.slice(0, length)}...` : text;
};

export const cn = (...classes: (string | undefined | null | boolean)[]): string => {
  return classes.filter(Boolean).join(" ");
};
