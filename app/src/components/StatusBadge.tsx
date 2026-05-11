interface StatusBadgeProps {
  status: string;
  children?: React.ReactNode;
}

const statusMap: Record<string, string> = {
  active: 'status-active',
  used: 'status-used',
  expired: 'status-expired',
  disabled: 'status-disabled',
  paused: 'status-paused',
  terminated: 'status-terminated',
  online: 'status-active',
  maintenance: 'status-warning',
  offline: 'status-expired',
};

export function StatusBadge({ status, children }: StatusBadgeProps) {
  const className = statusMap[status.toLowerCase()] || 'status-disabled';
  return (
    <span className={`status-badge ${className}`}>
      {children || status}
    </span>
  );
}
