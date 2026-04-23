import TabSwitcher from "@/components/workspace/TabSwitcher";

interface Props {
  right?: React.ReactNode;
}

/** Shared top strip on tool screens — tab switcher pills on the left, custom actions on the right. */
export default function ToolTopBar({ right }: Props) {
  return (
    <div className="flex items-center justify-between py-7">
      <TabSwitcher />
      {right && <div className="flex items-center gap-2">{right}</div>}
    </div>
  );
}
