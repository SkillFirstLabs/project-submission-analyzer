import React from 'react';

const Card = ({ children, className = '', glow = false, hoverable = false, ...props }) => {
  return (
    <div
      className={`card-gradient rounded-2xl p-6 ${
        glow ? 'shadow-[0_0_30px_rgba(92,79,229,0.15)]' : ''
      } ${
        hoverable ? 'card-gradient-hover cursor-pointer transform hover:-translate-y-0.5' : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
