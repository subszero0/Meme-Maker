import React, { useMemo, useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { VideoFormat } from "@/types/metadata";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface ResolutionSelectorProps {
  formats: VideoFormat[];
  onFormatChange: (formatId: string | null, resolution: string | null) => void;
}

export function ResolutionSelector({
  formats,
  onFormatChange,
}: ResolutionSelectorProps) {
  const [open, setOpen] = useState(false);
  const [selectedValue, setSelectedValue] = useState<string | null>(null);

  const uniqueFormats = useMemo(() => {
    const seen = new Set<string>();
    return formats.filter((format) => {
      if (!format.resolution || format.vcodec === "none") return false;
      if (format.acodec === "none") return false;
      if (seen.has(format.resolution)) return false;
      seen.add(format.resolution);
      return true;
    });
  }, [formats]);

  const handleSelect = useCallback(
    (format: VideoFormat) => {
      const formatId = format.format_id;
      const resolution = format.resolution;
      setSelectedValue(formatId);
      onFormatChange(formatId, resolution);
      setOpen(false);
    },
    [onFormatChange],
  );

  useEffect(() => {
    if (uniqueFormats.length > 0 && !selectedValue) {
      const defaultFormat =
        uniqueFormats.find((f) => f.resolution.includes("720")) ||
        uniqueFormats[0];
      if (defaultFormat) {
        handleSelect(defaultFormat);
      }
    }
  }, [uniqueFormats, selectedValue, handleSelect]);

  const selectedFormat = uniqueFormats.find(
    (f) => f.format_id === selectedValue,
  );

  return (
    <div className="space-y-2">
      <h3 className="text-sm text-gray-600 font-medium">Select Format</h3>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between"
          >
            {selectedValue
              ? selectedFormat?.resolution
              : "Select resolution..."}
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[--radix-popover-trigger-width] p-0">
          <Command>
            <CommandInput placeholder="Search resolution..." />
            <CommandList>
              <CommandEmpty>No resolutions found.</CommandEmpty>
              <CommandGroup>
                {uniqueFormats.map((format) => (
                  <CommandItem
                    key={format.format_id}
                    value={format.format_id}
                    onSelect={() => {
                      handleSelect(format);
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        selectedValue === format.format_id
                          ? "opacity-100"
                          : "opacity-0",
                      )}
                    />
                    {format.resolution || "Unknown"} ({format.ext || "mp4"})
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
